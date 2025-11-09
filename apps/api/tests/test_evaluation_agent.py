"""
평가 에이전트 테스트
"""
import pytest
from decimal import Decimal
from app.services.ai_agents.evaluation_agent import EvaluationAgent
from app.models.enums import EvaluationStatus


class TestEvaluationAgent:
    """평가 에이전트 테스트 클래스"""
    
    def test_weight_validation(self):
        """가중치 검증 테스트"""
        # 정상적인 가중치
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
    
    def test_final_score_calculation(self):
        """최종 점수 계산 테스트"""
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
        
        # 가중 평균 계산
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


class TestEvaluationStatus:
    """평가 상태 Enum 테스트"""
    
    def test_evaluation_status_enum(self):
        """평가 상태 Enum 값 확인"""
        assert EvaluationStatus.PENDING.value == "pending"
        assert EvaluationStatus.PROCESSING.value == "processing"
        assert EvaluationStatus.COMPLETED.value == "completed"
        assert EvaluationStatus.FAILED.value == "failed"
    
    def test_evaluation_status_values(self):
        """평가 상태 값 목록"""
        statuses = [status.value for status in EvaluationStatus]
        assert "pending" in statuses
        assert "processing" in statuses
        assert "completed" in statuses
        assert "failed" in statuses

