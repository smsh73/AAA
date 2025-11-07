"""
Evaluation report service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List

from app.models.evaluation_report import EvaluationReport
from app.schemas.evaluation_report import (
    EvaluationReportGenerateResponse,
    EvaluationReportResponse
)
from app.services.ai_agents.report_generation_agent import ReportGenerationAgent


class EvaluationReportService:
    """상세 평가보고서 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.report_agent = ReportGenerationAgent()

    async def generate_report(
        self,
        evaluation_id: UUID,
        include_sections: List[str],
        detail_level: str
    ) -> EvaluationReportGenerateResponse:
        """상세 평가보고서 생성"""
        report = EvaluationReport(
            evaluation_id=evaluation_id,
            report_type="detailed_evaluation",
            verification_status="pending"
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # 비동기 보고서 생성 시작 (Celery 작업)
        # await self.report_agent.generate_async(report.id, evaluation_id, include_sections, detail_level)

        return EvaluationReportGenerateResponse(
            report_id=report.id,
            status="generating",
            estimated_completion_time=datetime.utcnow() + timedelta(hours=2)
        )

    def get_report(self, report_id: UUID) -> Optional[EvaluationReport]:
        """상세 평가보고서 조회"""
        return self.db.query(EvaluationReport).filter(EvaluationReport.id == report_id).first()

