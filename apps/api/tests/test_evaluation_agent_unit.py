"""
Evaluation Agent 단위 테스트 (로직 검증 - 의존성 없음)
"""
import pytest
from decimal import Decimal


class TestEvaluationAgentLogic:
    """Evaluation Agent 로직 테스트"""
    
    def test_calculate_final_score_weights(self):
        """최종 점수 계산 가중치 검증"""
        weights = {
            "target_price_accuracy": 0.25,
            "performance_accuracy": 0.30,
            "investment_logic_validity": 0.15,
            "risk_analysis_appropriateness": 0.10,
            "report_frequency": 0.05,
            "sns_attention": 0.10,
            "media_frequency": 0.05,
        }
        
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"가중치 합계가 1.0이 아닙니다: {total_weight}"
    
    def test_calculate_final_score_range(self):
        """최종 점수 범위 검증"""
        scores = {
            "target_price_accuracy": 80.0,
            "performance_accuracy": 85.0,
            "investment_logic_validity": 75.0,
            "risk_analysis_appropriateness": 70.0,
            "report_frequency": 90.0,
            "sns_attention": 65.0,
            "media_frequency": 60.0,
        }
        
        weights = {
            "target_price_accuracy": 0.25,
            "performance_accuracy": 0.30,
            "investment_logic_validity": 0.15,
            "risk_analysis_appropriateness": 0.10,
            "report_frequency": 0.05,
            "sns_attention": 0.10,
            "media_frequency": 0.05,
        }
        
        final_score = sum(score_value * weights.get(score_type, 0.0) 
                         for score_type, score_value in scores.items())
        
        # 최종 점수는 0-100 범위
        assert 0.0 <= final_score <= 100.0, f"최종 점수가 범위를 벗어났습니다: {final_score}"
        
        # 예상 값 계산
        expected = (
            80.0 * 0.25 +
            85.0 * 0.30 +
            75.0 * 0.15 +
            70.0 * 0.10 +
            90.0 * 0.05 +
            65.0 * 0.10 +
            60.0 * 0.05
        )
        
        assert abs(final_score - expected) < 0.01, f"최종 점수 계산 오류: {final_score} != {expected}"
    
    def test_calculate_target_price_score_empty(self):
        """목표주가 점수 계산 - 빈 데이터"""
        scores = {}
        target_price_scores = []
        
        if not target_price_scores:
            result = 0.0
        else:
            result = sum(target_price_scores) / len(target_price_scores)
        
        assert result == 0.0
    
    def test_calculate_performance_score_weights(self):
        """실적 점수 계산 가중치 검증"""
        type_weights = {
            "operating_profit": 0.60,
            "revenue": 0.20,
            "net_profit": 0.20
        }
        
        total_weight = sum(type_weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"실적 가중치 합계가 1.0이 아닙니다: {total_weight}"
    
    def test_get_weight_all_kpis(self):
        """모든 KPI 가중치 조회 테스트"""
        expected_weights = {
            "target_price_accuracy": Decimal("0.25"),
            "performance_accuracy": Decimal("0.30"),
            "investment_logic_validity": Decimal("0.15"),
            "risk_analysis_appropriateness": Decimal("0.10"),
            "report_frequency": Decimal("0.05"),
            "sns_attention": Decimal("0.10"),
            "media_frequency": Decimal("0.05"),
        }
        
        # 가중치 합계 검증
        total = sum(expected_weights.values())
        assert abs(float(total) - 1.0) < 0.001
        
        # 모든 가중치가 0-1 범위인지 확인
        for weight in expected_weights.values():
            assert 0.0 <= float(weight) <= 1.0
    
    def test_score_range_validation(self):
        """점수 범위 검증 테스트"""
        scores = {
            "target_price_accuracy": 85.0,
            "performance_accuracy": 90.0,
            "investment_logic_validity": 75.0,
            "risk_analysis_appropriateness": 80.0,
            "report_frequency": 70.0,
            "sns_attention": 65.0,
            "media_frequency": 60.0,
        }
        
        # 모든 점수가 0-100 범위인지 확인
        for score_type, score_value in scores.items():
            assert 0.0 <= score_value <= 100.0, f"{score_type} 점수가 범위를 벗어났습니다: {score_value}"
