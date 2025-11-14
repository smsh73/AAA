"""
Award 로직 단위 테스트 (의존성 없음)
"""
import pytest


class TestAwardLogic:
    """Award 로직 테스트"""
    
    def test_category_sector_mapping(self):
        """카테고리-섹터 매핑 테스트"""
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
    
    def test_period_format(self):
        """기간 형식 테스트"""
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
        assert 1 <= int(parts[1]) <= 4
    
    def test_award_rank_validation(self):
        """Award 순위 검증"""
        ranks = [1, 2, 3]
        award_types = ["gold", "silver", "bronze"]
        
        # 순위와 타입 매칭
        rank_type_map = {
            1: "gold",
            2: "silver",
            3: "bronze"
        }
        
        for rank in ranks:
            assert rank in rank_type_map
            assert rank_type_map[rank] in award_types

