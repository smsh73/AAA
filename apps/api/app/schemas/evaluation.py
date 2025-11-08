"""
Evaluation schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date


class EvaluationStartRequest(BaseModel):
    report_id: UUID


class EvaluationResponse(BaseModel):
    evaluation_id: UUID
    status: str
    estimated_completion_time: Optional[datetime] = None


class EvaluationListResponse(BaseModel):
    evaluations: List[dict]
    total: int
    skip: int
    limit: int


class EvaluationDetailResponse(BaseModel):
    id: UUID
    report_id: UUID
    analyst_id: UUID
    company_id: Optional[UUID] = None
    evaluation_period: str
    evaluation_date: date
    final_score: Optional[float] = None
    ai_quantitative_score: Optional[float] = None
    sns_market_score: Optional[float] = None
    expert_survey_score: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EvaluationScoreResponse(BaseModel):
    id: UUID
    score_type: str
    score_value: float
    weight: float
    details: Optional[dict] = None
    reasoning: Optional[str] = None

    class Config:
        from_attributes = True

