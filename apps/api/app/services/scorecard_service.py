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
        
        # 정합성 검증
        self._validate_scorecard_data(analyst_id, company_id, period, evaluation_id)
        
        # 중복 체크
        existing = self.db.query(Scorecard).filter(
            Scorecard.analyst_id == analyst_id,
            Scorecard.period == period,
            Scorecard.company_id == company_id
        ).first()
        
        if existing:
            # 기존 스코어카드 업데이트
            existing.final_score = Decimal(str(final_score))
            existing.scorecard_data = {
                "evaluation_id": str(evaluation_id),
                "scores": scores,
                "summary": self._generate_summary(scores),
            }
            self.db.commit()
            self.db.refresh(existing)
            
            # 랭킹 업데이트
            self._update_rankings(period)
            
            return existing
        
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
    
    def _validate_scorecard_data(
        self,
        analyst_id: UUID,
        company_id: Optional[UUID],
        period: str,
        evaluation_id: UUID
    ):
        """스코어카드 데이터 정합성 검증"""
        from app.models.analyst import Analyst
        from app.models.evaluation import Evaluation
        
        # 애널리스트 존재 확인
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst {analyst_id} not found")
        
        # 기업 존재 확인
        if company_id:
            from app.models.company import Company
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError(f"Company {company_id} not found")
            
            # 애널리스트-기업 섹터 매칭 검증
            if analyst.sector and company.sector:
                if analyst.sector != company.sector:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"섹터 불일치: 애널리스트 섹터({analyst.sector}) != 기업 섹터({company.sector})"
                    )
        
        # 평가 존재 및 기간 일치 확인
        evaluation = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")
        
        if evaluation.evaluation_period != period:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"기간 불일치: 평가 기간({evaluation.evaluation_period}) != 스코어카드 기간({period})"
            )
        
        if evaluation.analyst_id != analyst_id:
            raise ValueError(
                f"애널리스트 불일치: 평가 애널리스트({evaluation.analyst_id}) != 스코어카드 애널리스트({analyst_id})"
            )

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

    async def recompute_analyst_scores(
        self,
        analyst_id: UUID,
        period: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """애널리스트 스코어 재계산"""
        from app.models.evaluation import Evaluation
        from app.services.ai_agents.evaluation_agent import EvaluationAgent
        
        evaluations = self.db.query(Evaluation).filter(
            Evaluation.analyst_id == analyst_id
        )
        
        if period:
            evaluations = evaluations.filter(Evaluation.evaluation_period == period)
        
        evaluations = evaluations.all()
        
        agent = EvaluationAgent(self.db)
        recomputed_count = 0
        
        for evaluation in evaluations:
            if force or not evaluation.final_score:
                await agent.evaluate_async(evaluation.id, evaluation.report_id)
                recomputed_count += 1
        
        return {
            "analyst_id": str(analyst_id),
            "period": period,
            "recomputed_count": recomputed_count,
            "total_evaluations": len(evaluations)
        }

    async def recompute_company_scores(
        self,
        company_id: UUID,
        period: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """기업 스코어 재계산"""
        from app.models.evaluation import Evaluation
        from app.services.ai_agents.evaluation_agent import EvaluationAgent
        
        evaluations = self.db.query(Evaluation).filter(
            Evaluation.company_id == company_id
        )
        
        if period:
            evaluations = evaluations.filter(Evaluation.evaluation_period == period)
        
        evaluations = evaluations.all()
        
        agent = EvaluationAgent(self.db)
        recomputed_count = 0
        
        for evaluation in evaluations:
            if force or not evaluation.final_score:
                await agent.evaluate_async(evaluation.id, evaluation.report_id)
                recomputed_count += 1
        
        return {
            "company_id": str(company_id),
            "period": period,
            "recomputed_count": recomputed_count,
            "total_evaluations": len(evaluations)
        }

    async def recompute_all_scores(
        self,
        period: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """전체 스코어 재계산"""
        from app.models.evaluation import Evaluation
        from app.services.ai_agents.evaluation_agent import EvaluationAgent
        
        evaluations = self.db.query(Evaluation)
        
        if period:
            evaluations = evaluations.filter(Evaluation.evaluation_period == period)
        
        evaluations = evaluations.all()
        
        agent = EvaluationAgent(self.db)
        recomputed_count = 0
        
        for evaluation in evaluations:
            if force or not evaluation.final_score:
                await agent.evaluate_async(evaluation.id, evaluation.report_id)
                recomputed_count += 1
        
        return {
            "period": period,
            "recomputed_count": recomputed_count,
            "total_evaluations": len(evaluations)
        }

    def get_scores(
        self,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        period: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """스코어 조회"""
        query = self.db.query(Scorecard)
        
        if analyst_id:
            query = query.filter(Scorecard.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Scorecard.company_id == company_id)
        if period:
            query = query.filter(Scorecard.period == period)
        
        scorecards = query.order_by(Scorecard.final_score.desc()).offset(skip).limit(limit).all()
        
        return [
            {
                "id": str(sc.id),
                "analyst_id": str(sc.analyst_id),
                "company_id": str(sc.company_id) if sc.company_id else None,
                "period": sc.period,
                "final_score": float(sc.final_score),
                "ranking": sc.ranking,
                "scorecard_data": sc.scorecard_data
            }
            for sc in scorecards
        ]

