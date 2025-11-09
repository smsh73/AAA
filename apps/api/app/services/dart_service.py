"""
OpenDART API 서비스 - 기업 실적 데이터 수집
"""
import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class DartService:
    """OpenDART API 서비스"""

    def __init__(self):
        self.api_key = os.getenv("DART_API_KEY")
        self.base_url = "https://opendart.fss.or.kr/api"
        self.timeout = 30.0

    async def get_company_info(self, corp_code: str) -> Dict[str, Any]:
        """기업 기본 정보 조회"""
        if not self.api_key:
            raise ValueError("DART_API_KEY not set")

        url = f"{self.base_url}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "000":
                    return data
                else:
                    raise ValueError(f"DART API 오류: {data.get('message', 'Unknown error')}")
        except httpx.TimeoutException:
            raise TimeoutError("DART API 요청 시간 초과")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"DART API HTTP 오류 ({e.response.status_code})")
        except httpx.RequestError as e:
            raise ConnectionError(f"DART API 연결 오류: {str(e)}")

    async def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011"  # 1분기: 11013, 반기: 11012, 3분기: 11014, 사업보고서: 11011
    ) -> Dict[str, Any]:
        """재무제표 조회"""
        if not self.api_key:
            raise ValueError("DART_API_KEY not set")

        url = f"{self.base_url}/fnlttSinglAcnt.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "fs_div": "CFS"  # CFS: 연결, OFS: 별도
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "000":
                    return data
                else:
                    raise ValueError(f"DART API 오류: {data.get('message', 'Unknown error')}")
        except httpx.TimeoutException:
            raise TimeoutError("DART API 요청 시간 초과")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"DART API HTTP 오류 ({e.response.status_code})")
        except httpx.RequestError as e:
            raise ConnectionError(f"DART API 연결 오류: {str(e)}")

    async def get_quarterly_performance(
        self,
        corp_code: str,
        bsns_year: str,
        reprt_code: str = "11011"
    ) -> Dict[str, Any]:
        """분기별 실적 조회"""
        financial_data = await self.get_financial_statements(corp_code, bsns_year, reprt_code)
        
        # 주요 재무 지표 추출
        result = {
            "corp_code": corp_code,
            "bsns_year": bsns_year,
            "reprt_code": reprt_code,
            "revenue": None,
            "operating_profit": None,
            "net_profit": None,
            "total_assets": None,
            "total_equity": None,
            "details": []
        }

        if "list" in financial_data:
            for item in financial_data["list"]:
                account_nm = item.get("account_nm", "")
                thstrm_amount = item.get("thstrm_amount", "")
                
                # 매출액
                if "매출액" in account_nm or "수익(매출액)" in account_nm:
                    result["revenue"] = self._parse_amount(thstrm_amount)
                
                # 영업이익
                if "영업이익" in account_nm:
                    result["operating_profit"] = self._parse_amount(thstrm_amount)
                
                # 당기순이익
                if "당기순이익" in account_nm or "순이익" in account_nm:
                    result["net_profit"] = self._parse_amount(thstrm_amount)
                
                # 총자산
                if "자산총계" in account_nm or "총자산" in account_nm:
                    result["total_assets"] = self._parse_amount(thstrm_amount)
                
                # 자본총계
                if "자본총계" in account_nm or "총자본" in account_nm:
                    result["total_equity"] = self._parse_amount(thstrm_amount)
                
                result["details"].append({
                    "account_nm": account_nm,
                    "thstrm_amount": thstrm_amount,
                    "frmtrm_amount": item.get("frmtrm_amount", ""),
                    "bfefrmtrm_amount": item.get("bfefrmtrm_amount", "")
                })

        return result

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """금액 문자열을 숫자로 변환"""
        if not amount_str or amount_str == "":
            return None
        
        try:
            # 쉼표 제거 후 숫자 변환
            amount_str = amount_str.replace(",", "")
            return float(amount_str)
        except (ValueError, AttributeError):
            return None

    async def search_company_by_name(self, company_name: str) -> List[Dict[str, Any]]:
        """기업명으로 검색"""
        if not self.api_key:
            raise ValueError("DART_API_KEY not set")

        url = f"{self.base_url}/company.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_name": company_name
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "000":
                    return data.get("list", [])
                else:
                    return []
        except Exception as e:
            print(f"DART 기업 검색 오류: {str(e)}")
            return []

