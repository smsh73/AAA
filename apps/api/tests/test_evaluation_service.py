"""
Evaluation Service 단위 테스트
"""
import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import date

from app.services.evaluation_service import EvaluationService
from app.models.evaluation import Evaluation, EvaluationScore
from app.models.enums import EvaluationStatus


class TestEvaluationService:
    """Evaluation Service 테스트"""
    
    def test_calculate_ai_quantitative_score(self, db_session, sample_evaluation, sample_evaluation_scores):
        """AI 정량 분석 점수 계산 테스트"""
        service = EvaluationService(db_session)
        
        scores = db_session.query(EvaluationScore).filter(
            EvaluationScore.evaluation_id == sample_evaluation.id
        ).all()
        
        ai_score = service._calculate_ai_quantitative_score(scores)
        
        # 가중 평균 계산 검증
        expected = (
            80.0 * 0.25 +
            85.0 * 0.30 +
            75.0 * 0.15 +
            70.0 * 0.10 +
            90.0 * 0.05 +
            65.0 * 0.10 +
            60.0 * 0.05
        )
        
        assert abs(float(ai_score) - expected) < 0.01
        assert 0.0 <= float(ai_score) <= 100.0
    
    def test_calculate_ai_quantitative_score_all_kpis(self, db_session, sample_evaluation, sample_evaluation_scores):
        """7개 KPI 모두 포함하는지 확인"""
        service = EvaluationService(db_session)
        
        scores = db_session.query(EvaluationScore).filter(
            EvaluationScore.evaluation_id == sample_evaluation.id
        ).all()
        
        # 7개 KPI 점수 타입 확인
        score_types = {score.score_type for score in scores}
        expected_types = {
            "target_price_accuracy",
            "performance_accuracy",
            "investment_logic_validity",
            "risk_analysis_appropriateness",
            "report_frequency",
            "sns_attention",
            "media_frequency"
        }
        
        assert score_types == expected_types
    
    def test_get_current_period(self, db_session):
        """현재 기간 계산 테스트"""
        service = EvaluationService(db_session)
        period = service._get_current_period()
        
        # 형식 검증: YYYY-QN
        assert "-Q" in period
        parts = period.split("-Q")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()
        assert 1 <= int(parts[1]) <= 4
    
    def test_get_evaluations(self, db_session, sample_evaluation):
        """평가 목록 조회 테스트"""
        service = EvaluationService(db_session)
        
        evaluations = service.get_evaluations()
        assert len(evaluations) >= 1
        assert any(e.id == sample_evaluation.id for e in evaluations)
    
    def test_get_evaluation(self, db_session, sample_evaluation):
        """평가 상세 조회 테스트"""
        service = EvaluationService(db_session)
        
        evaluation = service.get_evaluation(sample_evaluation.id)
        assert evaluation is not None
        assert evaluation.id == sample_evaluation.id
        assert evaluation.status == "completed"
    
    def test_get_evaluations_with_filters(self, db_session, sample_evaluation, sample_analyst):
        """필터링된 평가 목록 조회 테스트"""
        service = EvaluationService(db_session)
        
        # 애널리스트 필터
        evaluations = service.get_evaluations(analyst_id=sample_analyst.id)
        assert all(e.analyst_id == sample_analyst.id for e in evaluations)
        
        # 상태 필터
        evaluations = service.get_evaluations(status="completed")
        assert all(e.status == "completed" for e in evaluations)

