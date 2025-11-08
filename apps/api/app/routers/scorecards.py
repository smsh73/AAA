"""
Scorecards router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.scorecard import ScorecardResponse, ScorecardDetailResponse, ScorecardRankingResponse
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


@router.get("/{scorecard_id}", response_model=ScorecardDetailResponse)
async def get_scorecard(
    scorecard_id: UUID,
    db: Session = Depends(get_db)
):
    """스코어카드 상세 조회"""
    service = ScorecardService(db)
    scorecard = service.get_scorecard(scorecard_id)
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    return ScorecardDetailResponse.model_validate(scorecard)


@router.get("/ranking", response_model=ScorecardRankingResponse)
async def get_scorecard_ranking(
    period: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """스코어카드 랭킹 조회"""
    service = ScorecardService(db)
    rankings = service.get_rankings(period=period, limit=limit)
    return ScorecardRankingResponse(
        rankings=[ScorecardResponse.model_validate(s) for s in rankings],
        period=period or service._get_current_period(),
        total=len(rankings)
    )

