"""
KRX API 서비스 - 주가 데이터 수집
"""
import httpx
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json


class KrxService:
    """KRX API 서비스"""

    def __init__(self):
        self.base_url = "http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd"
        self.timeout = 30.0

    async def get_stock_price(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """일별 주가 데이터 조회"""
        url = self.base_url
        
        # 날짜 형식 변환 (YYYYMMDD)
        start_date_str = start_date.replace("-", "")
        end_date_str = end_date.replace("-", "")
        
        params = {
            "bld": "dbms/MDC/STAT/standard/MDCSTAT01501",
            "locale": "ko_KR",
            "trdDd": end_date_str,
            "strtDd": start_date_str,
            "isuCd": ticker,
            "isuCd2": "",
            "share": "1",
            "money": "1"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=params)
                response.raise_for_status()
                data = response.json()
                
                if "OutBlock_1" in data:
                    return self._parse_price_data(data["OutBlock_1"])
                else:
                    return []
        except httpx.TimeoutException:
            raise TimeoutError("KRX API 요청 시간 초과")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"KRX API HTTP 오류 ({e.response.status_code})")
        except httpx.RequestError as e:
            raise ConnectionError(f"KRX API 연결 오류: {str(e)}")
        except Exception as e:
            print(f"KRX 주가 데이터 조회 오류: {str(e)}")
            return []

    def _parse_price_data(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """주가 데이터 파싱"""
        result = []
        
        for item in data:
            try:
                date_str = item.get("TRD_DD", "")
                close_price = float(item.get("CLSPRC", 0))
                open_price = float(item.get("OPNPRC", 0))
                high_price = float(item.get("HGPRC", 0))
                low_price = float(item.get("LWPRC", 0))
                volume = int(item.get("ACC_TRDVOL", 0))
                change_rate = float(item.get("FLUC_RT", 0))
                
                result.append({
                    "date": date_str,
                    "close_price": close_price,
                    "open_price": open_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "volume": volume,
                    "change_rate": change_rate
                })
            except (ValueError, KeyError) as e:
                print(f"주가 데이터 파싱 오류: {str(e)}")
                continue
        
        return result

    async def get_current_price(self, ticker: str) -> Optional[float]:
        """현재 주가 조회"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        prices = await self.get_stock_price(ticker, yesterday, today)
        
        if prices:
            return prices[-1].get("close_price")
        return None

    async def get_price_range(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """기간별 주가 통계"""
        prices = await self.get_stock_price(ticker, start_date, end_date)
        
        if not prices:
            return {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "data_count": 0,
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "start_price": None,
                "end_price": None,
                "return_rate": None
            }
        
        close_prices = [p["close_price"] for p in prices if p["close_price"] > 0]
        
        if not close_prices:
            return {
                "ticker": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "data_count": 0,
                "min_price": None,
                "max_price": None,
                "avg_price": None,
                "start_price": None,
                "end_price": None,
                "return_rate": None
            }
        
        start_price = close_prices[0]
        end_price = close_prices[-1]
        min_price = min(close_prices)
        max_price = max(close_prices)
        avg_price = sum(close_prices) / len(close_prices)
        return_rate = ((end_price - start_price) / start_price * 100) if start_price > 0 else None
        
        return {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "data_count": len(prices),
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": round(avg_price, 2),
            "start_price": start_price,
            "end_price": end_price,
            "return_rate": round(return_rate, 2) if return_rate is not None else None
        }

