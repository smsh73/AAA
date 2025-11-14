"""
Scorecard Service 단위 테스트
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from app.services.scorecard_service import ScorecardService
from app.models.scorecard import Scorecard


class TestScorecardService:
    """Scorecard Service 테스트"""
    
    def test_get_scorecard(self, db_session, sample_scorecard):
        """스코어카드 상세 조회 테스트"""
        service = ScorecardService(db_session)
        
        scorecard = service.get_scorecard(sample_scorecard.id)
        assert scorecard is not None
        assert scorecard.id == sample_scorecard.id
        assert float(scorecard.final_score) == 85.50
    
    def test_get_scorecards(self, db_session, sample_scorecard, sample_analyst):
        """스코어카드 목록 조회 테스트"""
        service = ScorecardService(db_session)
        
        scorecards = service.get_scorecards(analyst_id=sample_analyst.id)
        assert len(scorecards) >= 1
        assert any(sc.id == sample_scorecard.id for sc in scorecards)
    
    def test_get_rankings(self, db_session, sample_scorecard):
        """랭킹 조회 테스트"""
        service = ScorecardService(db_session)
        
        rankings = service.get_rankings(period="2025-Q1")
        assert len(rankings) >= 1
        
        # 점수 내림차순 정렬 확인
        scores = [float(sc.final_score) for sc in rankings]
        assert scores == sorted(scores, reverse=True)
    
    def test_get_current_period(self, db_session):
        """현재 기간 계산 테스트"""
        service = ScorecardService(db_session)
        period = service._get_current_period()
        
        # 형식 검증: YYYY-QN
        assert "-Q" in period
        parts = period.split("-Q")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()
        assert 1 <= int(parts[1]) <= 4
    
    def test_create_scorecard_validation(self, db_session, sample_analyst, sample_company, sample_evaluation):
        """스코어카드 생성 검증 테스트"""
        service = ScorecardService(db_session)
        
        # 정상적인 스코어카드 생성
        scorecard = service.create_scorecard(
            evaluation_id=sample_evaluation.id,
            analyst_id=sample_analyst.id,
            company_id=sample_company.id,
            period="2025-Q1",
            final_score=90.0,
            scores={
                "target_price_accuracy": 85.0,
                "performance_accuracy": 90.0,
            }
        )
        
        assert scorecard is not None
        assert scorecard.analyst_id == sample_analyst.id
        assert scorecard.company_id == sample_company.id
        assert float(scorecard.final_score) == 90.0
        assert scorecard.period == "2025-Q1"
    
    def test_update_rankings(self, db_session, sample_scorecard):
        """랭킹 업데이트 테스트"""
        service = ScorecardService(db_session)
        
        # 랭킹 업데이트
        service._update_rankings("2025-Q1")
        
        # 업데이트된 스코어카드 확인
        updated = db_session.query(Scorecard).filter(
            Scorecard.id == sample_scorecard.id
        ).first()
        
        assert updated.ranking is not None
        assert updated.ranking >= 1

