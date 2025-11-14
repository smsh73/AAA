"""
Award schemas
"""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class AwardResponse(BaseModel):
    id: UUID
    scorecard_id: UUID
    analyst_id: UUID
    award_type: str
    award_category: str
    period: str
    rank: int

    class Config:
        from_attributes = True

