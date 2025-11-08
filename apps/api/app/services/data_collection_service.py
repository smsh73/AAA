"""
Data collection service
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import date

from app.services.perplexity_service import PerplexityService
from app.models.data_collection_log import DataCollectionLog
from app.schemas.data_collection import DataCollectionStatusResponse


class DataCollectionService:
    """데이터 수집 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.perplexity_service = PerplexityService()

    async def start_collection_for_analyst(self, analyst_id: UUID):
        """애널리스트별 자료수집 시작"""
        from app.models.analyst import Analyst
        from app.models.report import Report
        from app.services.ai_agents.data_collection_agent import DataCollectionAgent
        
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            return

        # 리포트 검색 및 다운로드
        reports = self.db.query(Report).filter(
            Report.analyst_id == analyst_id
        ).all()

        collection_agent = DataCollectionAgent(self.db)

        # 각 리포트별로 데이터 수집
        for report in reports:
            # 목표주가 데이터 수집
            if report.company_id:
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="target_price",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

                # 실적 데이터 수집
                await collection_agent.collect_data(
                    analyst_id=analyst_id,
                    collection_type="performance",
                    params={
                        "company_id": report.company_id,
                        "report_id": report.id,
                    }
                )

            # SNS 데이터 수집
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="sns",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report.publication_date.isoformat(),
                }
            )

            # 언론 데이터 수집
            await collection_agent.collect_data(
                analyst_id=analyst_id,
                collection_type="media",
                params={
                    "analyst_name": analyst.name,
                    "securities_firm": analyst.firm,
                    "report_title": report.title,
                    "report_date": report.publication_date.isoformat(),
                }
            )

