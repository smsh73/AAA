"""
Scorecard schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ScorecardResponse(BaseModel):
    id: UUID
    analyst_id: UUID
    company_id: Optional[UUID] = None
    market_id: Optional[UUID] = None
    period: str
    final_score: float
    ranking: Optional[int] = None

    class Config:
        from_attributes = True


class ScorecardDetailResponse(ScorecardResponse):
    scorecard_data: dict
    created_at: datetime
    updated_at: datetime


class ScorecardRankingResponse(BaseModel):
    rankings: List[ScorecardResponse]
    period: str
    total: int

