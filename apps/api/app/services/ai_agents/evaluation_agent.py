"""
Evaluation Agent - 평가 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.evaluation import Evaluation, EvaluationScore
from app.models.prediction import Prediction
from app.models.actual_result import ActualResult
from app.services.llm_service import LLMService
from app.services.perplexity_service import PerplexityService


class EvaluationAgent:
    """평가 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.perplexity_service = PerplexityService()

    async def evaluate_async(
        self,
        evaluation_id: UUID,
        report_id: UUID
    ) -> Dict[str, Any]:
        """비동기 평가 실행"""
        evaluation = self.db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise ValueError(f"Evaluation {evaluation_id} not found")

        # 1. 리포트에서 예측 정보 추출 (OpenAI)
        predictions = await self._extract_predictions(report_id)

        # 2. 실제 데이터 수집 (Perplexity)
        actual_results = await self._collect_actual_data(predictions)

        # 3. 근거 분석 (Claude)
        reasoning_scores = await self._analyze_reasoning(predictions)

        # 4. 정확도 계산 (Gemini)
        accuracy_scores = await self._calculate_accuracy(predictions, actual_results)

        # 5. 통합 Scoring
        scores = self._calculate_scores(accuracy_scores, reasoning_scores)

        # 6. 점수 저장
        for score_type, score_value in scores.items():
            eval_score = EvaluationScore(
                evaluation_id=evaluation_id,
                score_type=score_type,
                score_value=Decimal(str(score_value)),
                weight=self._get_weight(score_type),
            )
            self.db.add(eval_score)

        evaluation.status = "completed"
        self.db.commit()

        return {
            "evaluation_id": evaluation_id,
            "scores": scores,
            "status": "completed"
        }

    async def _extract_predictions(self, report_id: UUID) -> list:
        """예측 정보 추출 (OpenAI)"""
        # 리포트에서 예측 정보 추출
        predictions = self.db.query(Prediction).filter(
            Prediction.report_id == report_id
        ).all()
        
        if not predictions:
            # OpenAI로 리포트 파싱하여 예측 추출
            prompt = f"리포트 ID {report_id}에서 예측 정보를 추출하세요."
            result = await self.llm_service.generate("openai", prompt)
            # 결과 파싱하여 Prediction 생성
            # (실제 구현 필요)
        
        return predictions

    async def _collect_actual_data(self, predictions: list) -> list:
        """실제 데이터 수집 (Perplexity)"""
        actual_results = []
        
        for prediction in predictions:
            if prediction.prediction_type == "target_price":
                # 목표주가 데이터 수집
                data = await self.perplexity_service.collect_target_price_data(
                    company_name="",  # 실제로는 company 정보 필요
                    stock_code="",
                    prediction_period=prediction.period or "",
                    target_price=float(prediction.predicted_value)
                )
                # ActualResult 생성
                # (실제 구현 필요)
        
        return actual_results

    async def _analyze_reasoning(self, predictions: list) -> Dict[str, float]:
        """근거 분석 (Claude)"""
        reasoning_scores = {}
        
        for prediction in predictions:
            if prediction.reasoning:
                prompt = f"""
다음 예측 근거를 분석하여 논리적 타당성을 평가하세요 (0-100점):

예측: {prediction.prediction_type}
근거: {prediction.reasoning}

평가 기준:
- 논리적 일관성
- 근거의 구체성
- 데이터 기반 분석 여부
"""
                result = await self.llm_service.generate("claude", prompt)
                # 점수 추출 (실제 구현 필요)
                reasoning_scores[prediction.id] = 85.0
        
        return reasoning_scores

    async def _calculate_accuracy(
        self,
        predictions: list,
        actual_results: list
    ) -> Dict[str, float]:
        """정확도 계산 (Gemini)"""
        accuracy_scores = {}
        
        for prediction in predictions:
            actual = next(
                (r for r in actual_results if r.prediction_id == prediction.id),
                None
            )
            
            if actual:
                # 괴리율 계산
                if prediction.prediction_type == "target_price":
                    deviation_rate = abs(
                        (float(actual.actual_value) - float(prediction.predicted_value)) /
                        float(prediction.predicted_value) * 100
                    )
                    accuracy = max(0, 100 - deviation_rate)
                    accuracy_scores[prediction.id] = accuracy
                elif prediction.prediction_type in ["revenue", "operating_profit", "net_profit"]:
                    # 가중 평균 오차율 계산
                    error_rate = abs(
                        (float(actual.actual_value) - float(prediction.predicted_value)) /
                        abs(float(actual.actual_value)) * 100
                    )
                    accuracy = max(0, 100 - error_rate)
                    accuracy_scores[prediction.id] = accuracy
        
        return accuracy_scores

    def _calculate_scores(
        self,
        accuracy_scores: Dict[str, float],
        reasoning_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """통합 점수 계산"""
        # KPI별 점수 계산
        scores = {
            "target_price_accuracy": self._calculate_target_price_score(accuracy_scores),
            "performance_accuracy": self._calculate_performance_score(accuracy_scores),
            "investment_logic_validity": sum(reasoning_scores.values()) / len(reasoning_scores) if reasoning_scores else 0,
            "risk_analysis_appropriateness": 80.0,  # 실제 구현 필요
            "report_frequency": 85.0,  # 실제 구현 필요
            "sns_attention": 70.0,  # 실제 구현 필요
            "media_frequency": 65.0,  # 실제 구현 필요
        }
        
        return scores

    def _calculate_target_price_score(self, accuracy_scores: Dict[str, float]) -> float:
        """목표주가 정확도 점수 계산"""
        target_price_scores = [
            score for pred_id, score in accuracy_scores.items()
            # 실제로는 prediction_type으로 필터링 필요
        ]
        return sum(target_price_scores) / len(target_price_scores) if target_price_scores else 0

    def _calculate_performance_score(self, accuracy_scores: Dict[str, float]) -> float:
        """실적 추정 정확도 점수 계산 (가중 평균 오차율)"""
        # 1Q, 2Q, 3Q 가중치: 20%, 30%, 50%
        # 지표별 가중치: 영업이익 60%, 매출액 20%, 순이익 20%
        # 실제 구현 필요
        return 82.5

    def _get_weight(self, score_type: str) -> Decimal:
        """점수 타입별 가중치"""
        weights = {
            "target_price_accuracy": Decimal("0.25"),
            "performance_accuracy": Decimal("0.30"),
            "investment_logic_validity": Decimal("0.15"),
            "risk_analysis_appropriateness": Decimal("0.10"),
            "report_frequency": Decimal("0.05"),
            "sns_attention": Decimal("0.10"),
            "media_frequency": Decimal("0.05"),
        }
        return weights.get(score_type, Decimal("0.0"))
