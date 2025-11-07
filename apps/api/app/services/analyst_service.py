"""
Analyst service
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.analyst import Analyst
from app.schemas.analyst import AnalystCreate, AnalystResponse, AnalystBulkImportResponse
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

        # 자료수집 시작
        data_collection_started = False
        if created_analyst_ids:
            collection_service = DataCollectionService(self.db)
            for analyst_id in created_analyst_ids:
                await collection_service.start_collection_for_analyst(analyst_id)
            data_collection_started = True

        return AnalystBulkImportResponse(
            import_id=import_id,
            total_records=total_records,
            success_count=success_count,
            failed_count=failed_count,
            failed_records=failed_records,
            status="completed",
            data_collection_started=data_collection_started
        )

