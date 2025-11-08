"""
Award Agent - 어워드 선정 에이전트
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from app.models.scorecard import Scorecard
from app.models.award import Award
from app.services.llm_service import LLMService


class AwardAgent:
    """어워드 선정 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def select_awards(
        self,
        year: int,
        quarter: Optional[int] = None,
        categories: List[str] = None
    ) -> Dict[str, Any]:
        """어워드 선정"""
        categories = categories or ["AI", "2차전지", "방산", "IPO"]
        
        period = f"{year}-Q{quarter}" if quarter else str(year)
        
        winners = []
        runners_up = []
        
        for category in categories:
            # 카테고리별 스코어카드 조회
            scorecards = self.db.query(Scorecard).filter(
                Scorecard.period.like(f"{period}%")
            ).order_by(Scorecard.final_score.desc()).limit(10).all()
            
            if scorecards:
                # 1위 선정
                winner = scorecards[0]
                
                # 근거 생성 (Claude)
                evidence = await self._generate_evidence(winner, category)
                
                winners.append({
                    "category": category,
                    "analyst_id": winner.analyst_id,
                    "scorecard_id": winner.id,
                    "final_score": float(winner.final_score),
                    "evidence": evidence,
                })
                
                # Award 레코드 생성
                award = Award(
                    scorecard_id=winner.id,
                    analyst_id=winner.analyst_id,
                    award_type="gold",
                    award_category=category,
                    period=period,
                    rank=1,
                )
                self.db.add(award)
                
                # 2-3위 (Silver, Bronze)
                if len(scorecards) > 1:
                    runners_up.append({
                        "category": category,
                        "analyst_id": scorecards[1].analyst_id,
                        "rank": 2,
                    })
                    award_silver = Award(
                        scorecard_id=scorecards[1].id,
                        analyst_id=scorecards[1].analyst_id,
                        award_type="silver",
                        award_category=category,
                        period=period,
                        rank=2,
                    )
                    self.db.add(award_silver)
                
                if len(scorecards) > 2:
                    runners_up.append({
                        "category": category,
                        "analyst_id": scorecards[2].analyst_id,
                        "rank": 3,
                    })
                    award_bronze = Award(
                        scorecard_id=scorecards[2].id,
                        analyst_id=scorecards[2].analyst_id,
                        award_type="bronze",
                        award_category=category,
                        period=period,
                        rank=3,
                    )
                    self.db.add(award_bronze)
        
        self.db.commit()
        
        return {
            "winners": winners,
            "runners_up": runners_up,
            "period": period,
        }

    async def _generate_evidence(
        self,
        scorecard: Scorecard,
        category: str
    ) -> str:
        """수상 근거 생성 (Claude)"""
        prompt = f"""
다음 애널리스트의 수상 근거를 작성하세요:

카테고리: {category}
최종 점수: {scorecard.final_score}
스코어카드 데이터: {scorecard.scorecard_data}

근거 작성 요구사항:
- 구체적인 성과 지표 언급
- 객관적 데이터 기반
- 간결하고 명확한 문장
"""
        result = await self.llm_service.generate("claude", prompt)
        return result["content"]

