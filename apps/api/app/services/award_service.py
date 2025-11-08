"""
Award service
"""
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.award import Award
from app.schemas.award import AwardResponse
from app.services.ai_agents.award_agent import AwardAgent


class AwardService:
    """어워드 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.award_agent = AwardAgent(db)

    def get_awards(
        self,
        year: int,
        quarter: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Award]:
        """어워드 조회"""
        query = self.db.query(Award)

        if quarter:
            period = f"{year}-Q{quarter}"
        else:
            period = f"{year}"

        query = query.filter(Award.period.like(f"{period}%"))

        if category:
            query = query.filter(Award.award_category == category)

        return query.order_by(Award.rank).all()

    async def select_awards(
        self,
        year: int,
        quarter: Optional[int] = None,
        categories: Optional[List[str]] = None
    ) -> dict:
        """어워드 선정"""
        return await self.award_agent.select_awards(year, quarter, categories)

