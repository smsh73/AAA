"""
Perplexity API service
"""
import httpx
import os
from typing import Dict, Any, Optional


class PerplexityService:
    """Perplexity API 서비스"""

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.max_input_tokens = 1000000
        self.max_output_tokens = 100000

    async def search(
        self,
        prompt: str,
        model: str = "sonar",
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Perplexity 검색 실행"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens or self.max_output_tokens,
            "temperature": 0.2,
            "top_p": 0.9,
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Perplexity API 요청 시간 초과: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Perplexity API HTTP 오류 ({e.response.status_code}): {str(e)}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Perplexity API 연결 오류: {str(e)}")

    async def collect_target_price_data(
        self,
        company_name: str,
        stock_code: str,
        prediction_period: str,
        target_price: float
    ) -> Dict[str, Any]:
        """목표주가 정확성 데이터 수집"""
        prompt = f"""
당신은 한국 증권시장의 실적 데이터 수집 전문가입니다.

수집 목표:
- 기업명: {company_name}
- 종목코드: {stock_code}
- 예측 기간: {prediction_period}
- 목표주가: {target_price}

수집해야 할 데이터:
1. 해당 기간의 실제 주가 데이터 (일별, 주별, 월별)
2. 주가 변동 요인 (실적 발표, 뉴스, 시장 상황)
3. 목표주가 달성 여부 및 괴리율
4. 관련 뉴스 및 공시 정보

출력 형식: JSON
{{
  "company_name": "기업명",
  "stock_code": "종목코드",
  "prediction_period": "예측 기간",
  "target_price": 목표주가,
  "actual_prices": [
    {{
      "date": "날짜",
      "price": 실제주가,
      "deviation_rate": 괴리율
    }}
  ],
  "price_factors": ["주가 변동 요인"],
  "news_sources": ["뉴스 출처 URL"],
  "disclosure_sources": ["공시 출처 URL"]
}}

중요 사항:
- 모든 데이터는 출처를 명시해야 함
- 한국어와 영어 데이터 모두 수집
- DART, 한국거래소 등 공식 출처 우선
- 최신 데이터 우선
"""
        return await self.search(prompt)

