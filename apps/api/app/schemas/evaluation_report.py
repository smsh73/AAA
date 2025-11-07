"""
Evaluation report schemas
"""
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class EvaluationReportGenerateRequest(BaseModel):
    evaluation_id: UUID
    include_sections: List[str] = ["target_price", "performance", "sns", "media"]
    detail_level: str = "high"  # low, medium, high


class EvaluationReportGenerateResponse(BaseModel):
    report_id: UUID
    status: str
    estimated_completion_time: Optional[datetime] = None


class EvaluationReportResponse(BaseModel):
    report_id: UUID
    evaluation_id: UUID
    analyst_id: UUID
    company_id: Optional[UUID] = None
    report_date: datetime
    sections: List[dict]
    overall_evaluation: dict
    metadata: dict

