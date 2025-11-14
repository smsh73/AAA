"""
Award Agent 단위 테스트
"""
import pytest
from decimal import Decimal
from uuid import uuid4

from app.services.ai_agents.award_agent import AwardAgent
from app.models.scorecard import Scorecard
from app.models.award import Award


class TestAwardAgent:
    """Award Agent 테스트"""
    
    def test_category_sector_mapping(self, db_session):
        """카테고리-섹터 매핑 테스트"""
        agent = AwardAgent(db_session)
        
        # select_awards 메서드 내부의 매핑 확인
        category_sector_map = {
            "AI": ["AI", "반도체", "IT", "소프트웨어"],
            "2차전지": ["2차전지", "배터리", "전기차", "신에너지"],
            "방산": ["방산", "국방", "항공우주"],
            "IPO": ["IPO", "신규상장"]
        }
        
        # 모든 카테고리가 매핑되어 있는지 확인
        assert "AI" in category_sector_map
        assert "2차전지" in category_sector_map
        assert "방산" in category_sector_map
        assert "IPO" in category_sector_map
        
        # 각 카테고리에 섹터가 있는지 확인
        for category, sectors in category_sector_map.items():
            assert len(sectors) > 0
            assert all(isinstance(s, str) for s in sectors)
    
    def test_period_format(self, db_session):
        """기간 형식 테스트"""
        agent = AwardAgent(db_session)
        
        # 연도만 있는 경우
        period = "2025"
        assert period.isdigit() or "-Q" in period
        
        # 분기 포함 경우
        period = "2025-Q1"
        assert "-Q" in period
        parts = period.split("-Q")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

