"""
Data collection service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from app.services.perplexity_service import PerplexityService


class DataCollectionService:
    """데이터 수집 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.perplexity_service = PerplexityService()

    async def start_collection_for_analyst(self, analyst_id: UUID):
        """애널리스트별 자료수집 시작"""
        # 리포트 검색
        # 리포트 다운로드 및 파싱
        # 예측 정보 추출
        # 데이터 수집 시작 (각 KPI별)
        # 평가 프로세스 시작
        pass

