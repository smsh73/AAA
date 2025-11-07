"""
Scorecards router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.scorecard import ScorecardResponse
from app.services.scorecard_service import ScorecardService

router = APIRouter()


@router.get("", response_model=List[ScorecardResponse])
async def get_scorecards(
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    market_id: Optional[UUID] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """스코어카드 조회"""
    service = ScorecardService(db)
    return service.get_scorecards(
        analyst_id=analyst_id,
        company_id=company_id,
        market_id=market_id,
        period=period
    )

