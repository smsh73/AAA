"""
Analyst service
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.analyst import Analyst
from app.schemas.analyst import AnalystCreate, AnalystUpdate, AnalystResponse, AnalystBulkImportResponse
from app.services.data_collection_service import DataCollectionService


class AnalystService:
    """애널리스트 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_analysts(
        self,
        skip: int = 0,
        limit: int = 100,
        sector: Optional[str] = None,
        firm: Optional[str] = None
    ) -> List[Analyst]:
        """애널리스트 목록 조회"""
        query = self.db.query(Analyst)

        if sector:
            query = query.filter(Analyst.sector == sector)
        if firm:
            query = query.filter(Analyst.firm == firm)

        return query.offset(skip).limit(limit).all()

    def get_analyst(self, analyst_id: UUID) -> Optional[Analyst]:
        """애널리스트 조회"""
        return self.db.query(Analyst).filter(Analyst.id == analyst_id).first()

    def create_analyst(self, analyst_data: AnalystCreate) -> Analyst:
        """애널리스트 생성"""
        analyst = Analyst(**analyst_data.dict())
        self.db.add(analyst)
        self.db.commit()
        self.db.refresh(analyst)
        return analyst

    def update_analyst(self, analyst_id: UUID, analyst_data: AnalystUpdate) -> Optional[Analyst]:
        """애널리스트 수정"""
        analyst = self.get_analyst(analyst_id)
        if not analyst:
            return None
        
        update_data = analyst_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(analyst, key, value)
        
        self.db.commit()
        self.db.refresh(analyst)
        return analyst

    def delete_analyst(self, analyst_id: UUID) -> bool:
        """애널리스트 삭제 - 관련 데이터 확인 후 삭제"""
        analyst = self.get_analyst(analyst_id)
        if not analyst:
            return False
        
        # 관련 데이터 확인
        from app.models.report import Report
        from app.models.evaluation import Evaluation
        from app.models.scorecard import Scorecard
        from app.models.award import Award
        from app.models.data_collection_log import DataCollectionLog
        from app.models.collection_job import CollectionJob
        
        # 관련 리포트 확인
        reports_count = self.db.query(Report).filter(Report.analyst_id == analyst_id).count()
        evaluations_count = self.db.query(Evaluation).filter(Evaluation.analyst_id == analyst_id).count()
        scorecards_count = self.db.query(Scorecard).filter(Scorecard.analyst_id == analyst_id).count()
        awards_count = self.db.query(Award).filter(Award.analyst_id == analyst_id).count()
        
        # 관련 데이터가 있으면 삭제 불가
        if reports_count > 0 or evaluations_count > 0 or scorecards_count > 0 or awards_count > 0:
            raise ValueError(
                f"애널리스트를 삭제할 수 없습니다. 관련 데이터가 있습니다: "
                f"리포트 {reports_count}개, 평가 {evaluations_count}개, "
                f"스코어카드 {scorecards_count}개, 어워드 {awards_count}개"
            )
        
        # 데이터 수집 로그 및 작업 삭제 (CASCADE가 없을 수 있으므로)
        self.db.query(DataCollectionLog).filter(DataCollectionLog.analyst_id == analyst_id).delete()
        self.db.query(CollectionJob).filter(CollectionJob.analyst_id == analyst_id).delete()
        
        # 애널리스트 삭제
        self.db.delete(analyst)
        self.db.commit()
        return True

    async def bulk_import_and_start_collection(
        self,
        records: List[dict]
    ) -> AnalystBulkImportResponse:
        """일괄 등록 및 자료수집 시작"""
        import_id = uuid4()
        total_records = len(records)
        success_count = 0
        failed_count = 0
        failed_records = []

        created_analyst_ids = []

        for idx, record in enumerate(records):
            try:
                # 중복 체크
                existing = self.db.query(Analyst).filter(
                    Analyst.name == record.get("name"),
                    Analyst.firm == record.get("firm")
                ).first()

                if existing:
                    failed_records.append({
                        "row": idx + 1,
                        "analyst_name": record.get("name"),
                        "reason": "중복된 애널리스트"
                    })
                    failed_count += 1
                    continue

                # 애널리스트 생성
                analyst = Analyst(**record)
                self.db.add(analyst)
                self.db.flush()
                created_analyst_ids.append(analyst.id)
                success_count += 1

            except Exception as e:
                failed_records.append({
                    "row": idx + 1,
                    "analyst_name": record.get("name", "Unknown"),
                    "reason": str(e)
                })
                failed_count += 1

        self.db.commit()

        # 자료수집 시작 (Redis/Celery가 있는 경우에만)
        data_collection_started = False
        if created_analyst_ids:
            try:
                from app.tasks.data_collection_tasks import start_collection_for_analyst_task
                for analyst_id in created_analyst_ids:
                    # Celery 작업으로 비동기 실행
                    # Redis가 없으면 에러를 무시하고 애널리스트만 등록
                    start_collection_for_analyst_task.delay(str(analyst_id))
                data_collection_started = True
            except Exception as e:
                # Redis/Celery가 없거나 연결 실패 시 에러를 무시
                # 애널리스트는 이미 등록되었으므로 데이터 수집은 나중에 수동으로 시작 가능
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"데이터 수집 자동 시작 실패 (Redis/Celery 미사용 가능): {str(e)}")
                data_collection_started = False

        return AnalystBulkImportResponse(
            import_id=import_id,
            total_records=total_records,
            success_count=success_count,
            failed_count=failed_count,
            failed_records=failed_records,
            status="completed",
            data_collection_started=data_collection_started
        )

