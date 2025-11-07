"""
Evaluation schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class EvaluationStartRequest(BaseModel):
    report_id: UUID


class EvaluationResponse(BaseModel):
    evaluation_id: UUID
    status: str
    estimated_completion_time: Optional[datetime] = None

