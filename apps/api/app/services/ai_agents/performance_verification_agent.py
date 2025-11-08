"""
Performance Verification Agent - 실적 검증 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List
from decimal import Decimal

from app.models.prediction import Prediction
from app.models.actual_result import ActualResult
from app.services.llm_service import LLMService


class PerformanceVerificationAgent:
    """실적 검증 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    async def verify_performance(
        self,
        analyst_id: UUID,
        company_id: UUID,
        period: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
        """실적 검증"""
        # 예측 조회
        predictions = self.db.query(Prediction).filter(
            Prediction.company_id == company_id,
            Prediction.period == period
        ).all()

        # 실제 결과 조회
        actual_results = []
        for prediction in predictions:
            actual = self.db.query(ActualResult).filter(
                ActualResult.prediction_id == prediction.id
            ).first()
            if actual:
                actual_results.append(actual)

        # MAPE/Bias 계산
        mape = self._calculate_mape(predictions, actual_results)
        bias = self._calculate_bias(predictions, actual_results)
        hit_rate = self._calculate_hit_rate(predictions, actual_results)

        # 지표별 상세 분석 (Gemini)
        metrics_detail = await self._analyze_metrics_detail(
            predictions, actual_results, metrics
        )

        return {
            "mape": mape,
            "bias": bias,
            "hit_rate": hit_rate,
            "metrics_detail": metrics_detail,
        }

    def _calculate_mape(
        self,
        predictions: List[Prediction],
        actual_results: List[ActualResult]
    ) -> float:
        """MAPE (Mean Absolute Percentage Error) 계산"""
        if not predictions or not actual_results:
            return 0.0

        errors = []
        for prediction in predictions:
            actual = next(
                (r for r in actual_results if r.prediction_id == prediction.id),
                None
            )
            if actual and float(actual.actual_value) != 0:
                error = abs(
                    (float(actual.actual_value) - float(prediction.predicted_value)) /
                    float(actual.actual_value) * 100
                )
                errors.append(error)

        return sum(errors) / len(errors) if errors else 0.0

    def _calculate_bias(
        self,
        predictions: List[Prediction],
        actual_results: List[ActualResult]
    ) -> float:
        """Bias 계산"""
        if not predictions or not actual_results:
            return 0.0

        biases = []
        for prediction in predictions:
            actual = next(
                (r for r in actual_results if r.prediction_id == prediction.id),
                None
            )
            if actual:
                bias = (
                    (float(actual.actual_value) - float(prediction.predicted_value)) /
                    float(actual.actual_value) * 100
                )
                biases.append(bias)

        return sum(biases) / len(biases) if biases else 0.0

    def _calculate_hit_rate(
        self,
        predictions: List[Prediction],
        actual_results: List[ActualResult]
    ) -> float:
        """적중률 계산"""
        if not predictions or not actual_results:
            return 0.0

        hits = 0
        for prediction in predictions:
            actual = next(
                (r for r in actual_results if r.prediction_id == prediction.id),
                None
            )
            if actual:
                error_rate = abs(
                    (float(actual.actual_value) - float(prediction.predicted_value)) /
                    float(actual.actual_value) * 100
                )
                if error_rate <= 10:  # 10% 이내 오차를 적중으로 간주
                    hits += 1

        return (hits / len(predictions)) * 100 if predictions else 0.0

    async def _analyze_metrics_detail(
        self,
        predictions: List[Prediction],
        actual_results: List[ActualResult],
        metrics: List[str]
    ) -> List[Dict[str, Any]:
        """지표별 상세 분석 (Gemini)"""
        detail = []
        
        for metric in metrics:
            metric_predictions = [
                p for p in predictions if p.prediction_type == metric
            ]
            metric_actuals = [
                r for r in actual_results
                if any(r.prediction_id == p.id for p in metric_predictions)
            ]
            
            if metric_predictions and metric_actuals:
                prompt = f"""
다음 {metric} 예측과 실제 결과를 분석하세요:

예측: {[float(p.predicted_value) for p in metric_predictions]}
실제: {[float(a.actual_value) for a in metric_actuals]}

분석 항목:
- 예측 정확도
- 오차 패턴
- 개선 방안
"""
                result = await self.llm_service.generate("gemini", prompt)
                
                detail.append({
                    "metric": metric,
                    "analysis": result["content"],
                    "mape": self._calculate_mape(metric_predictions, metric_actuals),
                })
        
        return detail

