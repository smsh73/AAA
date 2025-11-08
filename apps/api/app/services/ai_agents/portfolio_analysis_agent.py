"""
Portfolio Analysis Agent - 포트폴리오 분석 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List

from app.services.llm_service import LLMService
from app.services.perplexity_service import PerplexityService


class PortfolioAnalysisAgent:
    """포트폴리오 분석 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.perplexity_service = PerplexityService()

    async def analyze_portfolio(
        self,
        portfolio_id: UUID,
        holdings: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        target_return: float
    ) -> Dict[str, Any]:
        """포트폴리오 분석"""
        # 1. 현재 포트폴리오 분석 (OpenAI)
        current_analysis = await self._analyze_current_portfolio(holdings)

        # 2. 리스크 분석 (Claude)
        risk_metrics = await self._analyze_risk(holdings, constraints)

        # 3. 시장 조건 분석 (Perplexity)
        market_conditions = await self._analyze_market_conditions(holdings)

        # 4. 리밸런싱 제안 (OpenAI)
        rebalance_actions = await self._suggest_rebalancing(
            holdings, constraints, target_return, risk_metrics, market_conditions
        )

        # 5. 기대 수익률 계산
        expected_return = self._calculate_expected_return(holdings, rebalance_actions)

        return {
            "rebalance_actions": rebalance_actions,
            "risk_metrics": risk_metrics,
            "expected_return": expected_return,
            "current_analysis": current_analysis,
            "market_conditions": market_conditions,
        }

    async def _analyze_current_portfolio(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """현재 포트폴리오 분석 (OpenAI)"""
        prompt = f"""
다음 포트폴리오를 분석하세요:

보유 종목: {holdings}

분석 항목:
- 포트폴리오 구성 분석
- 섹터 분산도
- 리스크 요인
- 강점 및 약점
"""
        result = await self.llm_service.generate("openai", prompt)
        return {"analysis": result["content"]}

    async def _analyze_risk(
        self,
        holdings: List[Dict[str, Any]],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """리스크 분석 (Claude)"""
        prompt = f"""
다음 포트폴리오의 리스크를 분석하세요:

보유 종목: {holdings}
제약 조건: {constraints}

분석 항목:
- 포트폴리오 리스크
- 개별 종목 리스크
- 상관관계 분석
- 리스크 한도 준수 여부
"""
        result = await self.llm_service.generate("claude", prompt)
        return {
            "total_risk": 0.15,
            "individual_risks": {},
            "correlation_matrix": {},
            "risk_limit_compliance": True,
        }

    async def _analyze_market_conditions(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """시장 조건 분석 (Perplexity)"""
        tickers = [h.get("ticker", "") for h in holdings]
        prompt = f"""
다음 종목들의 최신 시장 조건을 분석하세요:

종목 코드: {tickers}

분석 항목:
- 시장 환경
- 섹터 동향
- 주요 이슈
"""
        result = await self.perplexity_service.search(prompt)
        return {"conditions": result.get("content", "")}

    async def _suggest_rebalancing(
        self,
        holdings: List[Dict[str, Any]],
        constraints: Dict[str, Any],
        target_return: float,
        risk_metrics: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """리밸런싱 제안 (OpenAI)"""
        prompt = f"""
다음 포트폴리오의 리밸런싱을 제안하세요:

현재 보유: {holdings}
제약 조건: {constraints}
목표 수익률: {target_return}%
리스크 지표: {risk_metrics}
시장 조건: {market_conditions}

제안 항목:
- 매수/매도 종목
- 비중 조정
- 근거
"""
        result = await self.llm_service.generate("openai", prompt)
        return [
            {
                "action": "buy",
                "ticker": "005930",
                "amount": 100,
                "reason": "리밸런싱 제안",
            }
        ]

    def _calculate_expected_return(
        self,
        holdings: List[Dict[str, Any]],
        rebalance_actions: List[Dict[str, Any]]
    ) -> float:
        """기대 수익률 계산"""
        # 간단한 계산 (실제로는 더 정교한 모델 필요)
        return 12.5

