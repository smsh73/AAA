"""
Evaluation report service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.models.evaluation_report import EvaluationReport
from app.schemas.evaluation_report import (
    EvaluationReportGenerateResponse,
    EvaluationReportResponse
)
from app.services.ai_agents.report_generation_agent import ReportGenerationAgent
from app.models.evaluation_report import EvaluationReport
from app.models.evaluation import Evaluation
from app.tasks.evaluation_tasks import generate_evaluation_report_task


class EvaluationReportService:
    """상세 평가보고서 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.report_agent = ReportGenerationAgent(db)

    async def generate_report(
        self,
        evaluation_id: UUID,
        include_sections: List[str],
        detail_level: str
    ) -> EvaluationReportGenerateResponse:
        """상세 평가보고서 생성"""
        evaluation = self.db.query(Evaluation).filter(
            Evaluation.id == evaluation_id
        ).first()
        
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        report = EvaluationReport(
            evaluation_id=evaluation_id,
            analyst_id=evaluation.analyst_id,
            company_id=evaluation.company_id,
            report_type="detailed_evaluation",
            verification_status="pending"
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        # 비동기 보고서 생성 시작 (Celery 작업)
        generate_evaluation_report_task.delay(
            str(report.id),
            str(evaluation_id),
            include_sections,
            detail_level
        )

        return EvaluationReportGenerateResponse(
            report_id=report.id,
            status="generating",
            estimated_completion_time=datetime.utcnow() + timedelta(hours=2)
        )

    def get_report(self, report_id: UUID) -> Optional[dict]:
        """상세 평가보고서 조회"""
        from app.models.analyst import Analyst
        from app.models.company import Company
        
        report = self.db.query(EvaluationReport).filter(
            EvaluationReport.id == report_id
        ).first()
        
        if not report:
            return None
        
        # 리포트 응답 형식으로 변환
        analyst = self.db.query(Analyst).filter(Analyst.id == report.analyst_id).first()
        company = None
        if report.company_id:
            company = self.db.query(Company).filter(Company.id == report.company_id).first()
        
        return {
            "report_id": report.id,
            "evaluation_id": report.evaluation_id,
            "analyst_name": analyst.name if analyst else "",
            "company_name": company.name_kr if company else None,
            "report_date": report.created_at.isoformat(),
            "sections": report.report_content.get("sections", []) if report.report_content else [],
            "overall_evaluation": report.report_content.get("overall_evaluation", {}) if report.report_content else {},
            "metadata": {
                "data_sources_count": report.data_sources_count or 0,
                "verification_status": report.verification_status,
                "report_quality_score": float(report.report_quality_score) if report.report_quality_score else 0,
                "generated_by": report.generated_by or [],
            }
        }

