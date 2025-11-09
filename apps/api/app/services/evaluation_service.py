"""
Evaluation service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from app.models.evaluation import Evaluation, EvaluationScore
from app.models.enums import EvaluationStatus
from app.models.report import Report
from app.schemas.evaluation import EvaluationResponse
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.services.ai_agents.data_collection_agent import DataCollectionAgent
from app.services.scorecard_service import ScorecardService
from app.models.data_collection_log import DataCollectionLog
from app.tasks.evaluation_tasks import evaluate_report_task


class EvaluationService:
    """평가 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluation_agent = EvaluationAgent(db)
        self.data_collection_agent = DataCollectionAgent(db)
        self.scorecard_service = ScorecardService(db)

    async def start_evaluation(self, report_id: UUID) -> EvaluationResponse:
        """평가 시작"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 중복 평가 방지 (활성 상태만 체크)
        existing = self.db.query(Evaluation).filter(
            Evaluation.report_id == report_id,
            Evaluation.status.in_([EvaluationStatus.PENDING.value, EvaluationStatus.PROCESSING.value])
        ).first()
        
        if existing:
            raise ValueError(f"이미 진행 중인 평가가 있습니다: {existing.id}")
        
        evaluation = Evaluation(
            report_id=report_id,
            analyst_id=report.analyst_id,
            company_id=report.company_id,
            evaluation_period=self._get_current_period(),
            evaluation_date=datetime.now().date(),
            status=EvaluationStatus.PROCESSING.value
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        # 비동기 평가 시작 (Celery 작업)
        evaluate_report_task.delay(str(evaluation.id), str(report_id))

        return EvaluationResponse(
            evaluation_id=evaluation.id,
            status="processing",
            estimated_completion_time=datetime.utcnow() + timedelta(hours=1)
        )

    async def complete_evaluation(
        self,
        evaluation_id: UUID
    ) -> Dict[str, Any]:
        """평가 완료 및 스코어카드 생성"""
        evaluation = self.db.query(Evaluation).filter(
            Evaluation.id == evaluation_id
        ).first()
        
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # 평가 점수 조회
        scores = self.db.query(EvaluationScore).filter(
            EvaluationScore.evaluation_id == evaluation_id
        ).all()

        # 1단계: AI 정량 분석 점수 (40%)
        ai_quantitative_score = self._calculate_ai_quantitative_score(scores)

        # 2단계: SNS·시장 반응 점수 (30%)
        sns_market_score = await self._calculate_sns_market_score(evaluation)

        # 3단계: 전문가 평가 및 설문 점수 (30%)
        expert_survey_score = await self._calculate_expert_survey_score(evaluation)

        # 최종 점수 계산
        final_score = (
            ai_quantitative_score * Decimal("0.40") +
            sns_market_score * Decimal("0.30") +
            expert_survey_score * Decimal("0.30")
        )

        # 스코어카드 생성
        scorecard = self.scorecard_service.create_scorecard(
            evaluation_id=evaluation_id,
            analyst_id=evaluation.analyst_id,
            company_id=evaluation.company_id,
            period=evaluation.evaluation_period,
            final_score=float(final_score),
            scores={
                "ai_quantitative_score": float(ai_quantitative_score),
                "sns_market_score": float(sns_market_score),
                "expert_survey_score": float(expert_survey_score),
            }
        )

        evaluation.status = EvaluationStatus.COMPLETED.value
        self.db.commit()

        return {
            "evaluation_id": evaluation_id,
            "final_score": float(final_score),
            "ai_quantitative_score": float(ai_quantitative_score),
            "sns_market_score": float(sns_market_score),
            "expert_survey_score": float(expert_survey_score),
            "scorecard_id": scorecard.id,
        }

    def _calculate_ai_quantitative_score(
        self,
        scores: list
    ) -> Decimal:
        """AI 정량 분석 점수 계산"""
        # KPI별 가중 평균
        weights = {
            "target_price_accuracy": Decimal("0.25"),
            "performance_accuracy": Decimal("0.30"),
            "investment_logic_validity": Decimal("0.15"),
            "risk_analysis_appropriateness": Decimal("0.10"),
            "report_frequency": Decimal("0.05"),
        }
        
        total_score = Decimal("0")
        total_weight = Decimal("0")
        
        for score in scores:
            weight = weights.get(score.score_type, Decimal("0"))
            if weight > 0:
                total_score += score.score_value * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else Decimal("0")

    async def _calculate_sns_market_score(
        self,
        evaluation: Evaluation
    ) -> Decimal:
        """SNS·시장 반응 점수 계산"""
        # SNS 주목도 (10%) + 언론 빈도 (5%) = 15%
        # 전체 30% 중 15%이므로 0.5 가중치
        
        # DataCollectionLog에서 SNS/Media 데이터 조회
        sns_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == evaluation.analyst_id,
            DataCollectionLog.collection_type == "sns",
            DataCollectionLog.status == "success"
        ).all()
        
        media_logs = self.db.query(DataCollectionLog).filter(
            DataCollectionLog.analyst_id == evaluation.analyst_id,
            DataCollectionLog.collection_type == "media",
            DataCollectionLog.status == "success"
        ).all()
        
        # 점수 계산 (실제로는 수집된 데이터 기반 계산)
        sns_score = Decimal("75.0")
        if sns_logs:
            # 수집된 데이터에서 점수 계산
            # 실제 구현 필요
            pass
        
        media_score = Decimal("70.0")
        if media_logs:
            # 수집된 데이터에서 점수 계산
            # 실제 구현 필요
            pass
        
        return (sns_score * Decimal("0.10") + media_score * Decimal("0.05")) / Decimal("0.15")

    async def _calculate_expert_survey_score(
        self,
        evaluation: Evaluation
    ) -> Decimal:
        """전문가 평가 및 설문 점수 계산"""
        # 실제로는 설문 데이터에서 조회
        return Decimal("80.0")

    def get_evaluations(
        self,
        skip: int = 0,
        limit: int = 100,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[Evaluation]:
        """평가 목록 조회"""
        query = self.db.query(Evaluation)

        if analyst_id:
            query = query.filter(Evaluation.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Evaluation.company_id == company_id)
        if status:
            query = query.filter(Evaluation.status == status)

        return query.order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()

    def get_evaluations_count(
        self,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> int:
        """평가 총 개수"""
        query = self.db.query(Evaluation)

        if analyst_id:
            query = query.filter(Evaluation.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Evaluation.company_id == company_id)
        if status:
            query = query.filter(Evaluation.status == status)

        return query.count()

    def get_evaluation(self, evaluation_id: UUID) -> Optional[Evaluation]:
        """평가 상세 조회"""
        return self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()

    def _get_current_period(self) -> str:
        """현재 기간 계산"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"{now.year}-Q{quarter}"
