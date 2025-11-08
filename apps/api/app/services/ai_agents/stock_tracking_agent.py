"""
Stock Tracking Agent - 추천종목 추적 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models.prediction import Prediction
from app.services.llm_service import LLMService
from app.services.perplexity_service import PerplexityService


class StockTrackingAgent:
    """추천종목 추적 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.perplexity_service = PerplexityService()

    async def track_stock(
        self,
        recommendation_id: UUID,
        tracking_period: int,
        benchmark_id: UUID = None
    ) -> Dict[str, Any]:
        """추천 종목 추적"""
        prediction = self.db.query(Prediction).filter(
            Prediction.id == recommendation_id
        ).first()
        
        if not prediction:
            raise ValueError(f"Prediction {recommendation_id} not found")

        # 1. 주가 데이터 수집 (Perplexity)
        price_data = await self._collect_price_data(
            prediction.company_id, tracking_period
        )

        # 2. 수익률 계산
        returns = self._calculate_returns(price_data)

        # 3. 최대 낙폭 계산
        max_drawdown = self._calculate_max_drawdown(price_data)

        # 4. 샤프 지수 계산
        sharpe = self._calculate_sharpe(price_data)

        # 5. 벤치마크 대비 수익률
        benchmark_diff = 0.0
        if benchmark_id:
            benchmark_data = await self._collect_price_data(benchmark_id, tracking_period)
            benchmark_returns = self._calculate_returns(benchmark_data)
            benchmark_diff = returns - benchmark_returns

        # 6. 시장 변동 이슈 분석 (Perplexity)
        market_issues = await self._analyze_market_issues(
            prediction.company_id, tracking_period
        )

        return {
            "returns": returns,
            "max_drawdown": max_drawdown,
            "sharpe": sharpe,
            "benchmark_diff": benchmark_diff,
            "market_issues": market_issues,
        }

    async def _collect_price_data(
        self,
        company_id: UUID,
        period_days: int
    ) -> List[Dict[str, Any]]:
        """주가 데이터 수집"""
        prompt = f"""
다음 기업의 최근 {period_days}일간 주가 데이터를 수집하세요:

기업 ID: {company_id}

수집 항목:
- 일별 종가
- 거래량
- 변동률
"""
        result = await self.perplexity_service.search(prompt)
        # 실제로는 JSON 파싱 필요
        return []

    def _calculate_returns(self, price_data: List[Dict[str, Any]]) -> float:
        """수익률 계산"""
        if not price_data or len(price_data) < 2:
            return 0.0
        
        start_price = price_data[0].get("price", 0)
        end_price = price_data[-1].get("price", 0)
        
        if start_price == 0:
            return 0.0
        
        return ((end_price - start_price) / start_price) * 100

    def _calculate_max_drawdown(self, price_data: List[Dict[str, Any]]) -> float:
        """최대 낙폭 계산"""
        if not price_data:
            return 0.0
        
        prices = [d.get("price", 0) for d in price_data]
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices:
            if price > peak:
                peak = price
            dd = ((peak - price) / peak) * 100
            if dd > max_dd:
                max_dd = dd
        
        return max_dd

    def _calculate_sharpe(self, price_data: List[Dict[str, Any]]) -> float:
        """샤프 지수 계산"""
        if not price_data or len(price_data) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(price_data)):
            prev_price = price_data[i-1].get("price", 0)
            curr_price = price_data[i].get("price", 0)
            if prev_price > 0:
                ret = (curr_price - prev_price) / prev_price
                returns.append(ret)
        
        if not returns:
            return 0.0
        
        avg_return = sum(returns) / len(returns)
        
        # 표준편차 계산
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        # 무위험 수익률을 0으로 가정
        sharpe = (avg_return / std_dev) * (252 ** 0.5)  # 연율화
        
        return sharpe

    async def _analyze_market_issues(
        self,
        company_id: UUID,
        period_days: int
    ) -> List[str]:
        """시장 변동 이슈 분석"""
        prompt = f"""
다음 기업의 최근 {period_days}일간 주요 시장 이슈를 분석하세요:

기업 ID: {company_id}

분석 항목:
- 주가 변동 요인
- 주요 뉴스
- 시장 환경 변화
"""
        result = await self.perplexity_service.search(prompt)
        # 실제로는 JSON 파싱 필요
        return []

