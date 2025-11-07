"""
Scorecard service
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.scorecard import Scorecard
from app.schemas.scorecard import ScorecardResponse


class ScorecardService:
    """스코어카드 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_scorecards(
        self,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        market_id: Optional[UUID] = None,
        period: Optional[str] = None
    ) -> List[Scorecard]:
        """스코어카드 조회"""
        query = self.db.query(Scorecard)

        if analyst_id:
            query = query.filter(Scorecard.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Scorecard.company_id == company_id)
        if market_id:
            query = query.filter(Scorecard.market_id == market_id)
        if period:
            query = query.filter(Scorecard.period == period)

        return query.order_by(Scorecard.final_score.desc()).all()

