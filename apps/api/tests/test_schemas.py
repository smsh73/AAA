"""
Schema 정합성 테스트
"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.schemas.evaluation import EvaluationDetailResponse, EvaluationScoreResponse
from app.schemas.award import AwardResponse
from app.schemas.scorecard import ScorecardResponse


class TestSchemas:
    """Schema 테스트"""
    
    def test_evaluation_detail_response(self):
        """EvaluationDetailResponse 스키마 테스트"""
        data = {
            "id": uuid4(),
            "report_id": uuid4(),
            "analyst_id": uuid4(),
            "company_id": uuid4(),
            "evaluation_period": "2025-Q1",
            "evaluation_date": datetime.now().date(),
            "final_score": 85.5,
            "ai_quantitative_score": 80.0,
            "sns_market_score": 75.0,
            "expert_survey_score": 80.0,
            "status": "completed",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        response = EvaluationDetailResponse(**data)
        assert response.id == data["id"]
        assert response.final_score == 85.5
        assert response.status == "completed"
    
    def test_evaluation_score_response(self):
        """EvaluationScoreResponse 스키마 테스트"""
        data = {
            "id": uuid4(),
            "score_type": "target_price_accuracy",
            "score_value": 80.0,
            "weight": 0.25,
            "details": {"accuracy": 0.85},
            "reasoning": "목표주가 정확도 계산"
        }
        
        response = EvaluationScoreResponse(**data)
        assert response.score_type == "target_price_accuracy"
        assert response.score_value == 80.0
        assert response.weight == 0.25
    
    def test_award_response(self):
        """AwardResponse 스키마 테스트"""
        data = {
            "id": uuid4(),
            "scorecard_id": uuid4(),
            "analyst_id": uuid4(),
            "award_type": "gold",
            "award_category": "AI",
            "period": "2025-Q1",
            "rank": 1
        }
        
        response = AwardResponse(**data)
        assert response.award_type == "gold"
        assert response.award_category == "AI"
        assert response.rank == 1
        assert response.scorecard_id == data["scorecard_id"]  # 추가된 필드 확인
    
    def test_scorecard_response(self):
        """ScorecardResponse 스키마 테스트"""
        data = {
            "id": uuid4(),
            "analyst_id": uuid4(),
            "company_id": uuid4(),
            "market_id": None,
            "period": "2025-Q1",
            "final_score": 85.5,
            "ranking": 1
        }
        
        response = ScorecardResponse(**data)
        assert response.period == "2025-Q1"
        assert response.final_score == 85.5
        assert response.ranking == 1

