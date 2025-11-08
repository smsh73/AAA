"""
Scorecard service
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime

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

    def get_scorecard(self, scorecard_id: UUID) -> Optional[Scorecard]:
        """스코어카드 상세 조회"""
        return self.db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()

    def get_rankings(
        self,
        period: Optional[str] = None,
        limit: int = 100
    ) -> List[Scorecard]:
        """랭킹 조회"""
        query = self.db.query(Scorecard)
        
        if period:
            query = query.filter(Scorecard.period == period)
        
        return query.order_by(Scorecard.final_score.desc()).limit(limit).all()

    def _get_current_period(self) -> str:
        """현재 기간 계산"""
        from datetime import datetime
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"

    def create_scorecard(
        self,
        evaluation_id: UUID,
        analyst_id: UUID,
        company_id: Optional[UUID],
        period: str,
        final_score: float,
        scores: Dict[str, float]
    ) -> Scorecard:
        """스코어카드 생성"""
        from decimal import Decimal
        
        scorecard = Scorecard(
            analyst_id=analyst_id,
            company_id=company_id,
            period=period,
            final_score=Decimal(str(final_score)),
            scorecard_data={
                "evaluation_id": str(evaluation_id),
                "scores": scores,
                "summary": self._generate_summary(scores),
            }
        )
        self.db.add(scorecard)
        self.db.commit()
        self.db.refresh(scorecard)

        # 랭킹 업데이트
        self._update_rankings(period)

        return scorecard

    def _generate_summary(self, scores: Dict[str, float]) -> str:
        """스코어카드 요약 생성"""
        top_score = max(scores.items(), key=lambda x: x[1])
        return f"최고 점수: {top_score[0]} ({top_score[1]:.2f}점)"

    def _update_rankings(self, period: str):
        """랭킹 업데이트"""
        scorecards = self.db.query(Scorecard).filter(
            Scorecard.period == period
        ).order_by(Scorecard.final_score.desc()).all()

        for rank, scorecard in enumerate(scorecards, 1):
            scorecard.ranking = rank
        
        self.db.commit()

