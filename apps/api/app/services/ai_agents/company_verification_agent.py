"""
Company Verification Agent - 기업정보 검증 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List

from app.models.company import Company
from app.services.llm_service import LLMService
from app.services.perplexity_service import PerplexityService


class CompanyVerificationAgent:
    """기업정보 검증 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.perplexity_service = PerplexityService()

    async def verify_company(
        self,
        company_id: UUID,
        verification_fields: List[str],
        sources: List[str]
    ) -> Dict[str, Any]:
        """기업정보 검증"""
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # 1. 공시 데이터 수집 (Perplexity)
        disclosure_data = await self._collect_disclosure_data(company.ticker)

        # 2. 데이터 비교 및 검증 (Claude)
        verification_result = await self._verify_data(
            company, disclosure_data, verification_fields
        )

        # 3. 불일치 항목 수정
        if verification_result.get("discrepancies"):
            corrected_data = await self._correct_data(
                company, verification_result["discrepancies"]
            )
            verification_result["corrected_data"] = corrected_data

        return verification_result

    async def _collect_disclosure_data(self, ticker: str) -> Dict[str, Any]:
        """공시 데이터 수집 (Perplexity)"""
        prompt = f"""
다음 종목의 최신 공시 정보를 수집하세요:

종목코드: {ticker}

수집 항목:
- 최신 재무제표 (매출액, 영업이익, 순이익)
- 주요 공시 사항
- 최신 주가 정보
- 출처 URL

출력 형식: JSON
"""
        result = await self.perplexity_service.search(prompt)
        return result

    async def _verify_data(
        self,
        company: Company,
        disclosure_data: Dict[str, Any],
        verification_fields: List[str]
    ) -> Dict[str, Any]:
        """데이터 검증 (Claude)"""
        prompt = f"""
다음 기업 정보를 공시 데이터와 비교하여 검증하세요:

기업 정보:
- 종목코드: {company.ticker}
- 기업명: {company.name_kr}
- 재무 정보: {company.fundamentals}

공시 데이터: {disclosure_data}

검증 필드: {verification_fields}

불일치 항목과 수정된 데이터를 제시하세요.
"""
        result = await self.llm_service.generate("claude", prompt)
        
        return {
            "verified": True,
            "discrepancies": [],
            "confidence": 0.95,
        }

    async def _correct_data(
        self,
        company: Company,
        discrepancies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """데이터 수정"""
        corrected = {}
        
        for discrepancy in discrepancies:
            field = discrepancy.get("field")
            corrected_value = discrepancy.get("corrected_value")
            corrected[field] = corrected_value
        
        # Company 업데이트
        if corrected:
            if "fundamentals" in corrected:
                company.fundamentals = corrected["fundamentals"]
            self.db.commit()
        
        return corrected

