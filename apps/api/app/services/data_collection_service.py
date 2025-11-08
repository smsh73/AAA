"""
Data collection service
"""
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta

from app.services.perplexity_service import PerplexityService
from app.models.data_collection_log import DataCollectionLog
from app.models.collection_job import CollectionJob
from app.schemas.data_collection import DataCollectionStartResponse, DataCollectionStatusResponse


class DataCollectionService:
    """데이터 수집 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.perplexity_service = PerplexityService()

    async def start_collection(
        self,
        analyst_id: UUID,
        collection_types: List[str],
        start_date: date,
        end_date: date
    ) -> DataCollectionStartResponse:
        """데이터 수집 작업 시작"""
        from app.models.analyst import Analyst
        from app.tasks.data_collection_tasks import start_collection_job_task
        
        # 애널리스트 존재 확인
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_id}")
        
        # CollectionJob 생성
        job = CollectionJob(
            analyst_id=analyst_id,
            collection_types=collection_types,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.max.time()),
            status="pending",
            progress={ct: {"total": 0, "completed": 0, "failed": 0} for ct in collection_types},
            overall_progress="0.0"
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # 예상 완료 시간 계산 (각 타입당 평균 5분 가정)
        estimated_minutes = len(collection_types) * 5
        estimated_completion = datetime.now() + timedelta(minutes=estimated_minutes)
        job.estimated_completion_time = estimated_completion
        self.db.commit()
        
        # Celery 태스크 시작
        start_collection_job_task.delay(str(job.id))
        
        return DataCollectionStartResponse(
            collection_job_id=job.id,
            status=job.status,
            estimated_completion_time=job.estimated_completion_time
        )

    def get_collection_status(self, collection_job_id: UUID) -> Optional[DataCollectionStatusResponse]:
        """데이터 수집 작업 상태 조회"""
        job = self.db.query(CollectionJob).filter(CollectionJob.id == collection_job_id).first()
        if not job:
            return None
        
        # 전체 진행률 계산
        total_tasks = 0
        completed_tasks = 0
        
        for ct, progress in job.progress.items():
            total = progress.get("total", 0)
            completed = progress.get("completed", 0)
            total_tasks += total
            completed_tasks += completed
        
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        return DataCollectionStatusResponse(
            collection_job_id=job.id,
            status=job.status,
            progress=job.progress,
            overall_progress=overall_progress,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )

    async def start_collection_for_analyst(self, analyst_id: UUID):
        """애널리스트별 자료수집 시작"""
        from app.models.analyst import Analyst
        from app.models.report import Report
        from app.services.ai_agents.data_collection_agent import DataCollectionAgent
        
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            return

        # 리포트 검색 및 다운로드
        reports = self.db.query(Report).filter(
            Report.analyst_id == analyst_id
        ).all()

        collection_agent = DataCollectionAgent(self.db)

        # 각 리포트별로 데이터 수집
        for report in reports:
            # 목표주가 데이터 수집
            if report.company_id:
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="target_price",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

                # 실적 데이터 수집
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="performance",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

            # SNS 데이터 수집
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="sns",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report.publication_date.isoformat(),
                }
            )

            # 언론 데이터 수집
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="media",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report.publication_date.isoformat(),
                }
            )

