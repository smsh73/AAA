"""
증권사 사이트 크롤링 서비스 - 애널리스트 리포트 검색
"""
import httpx
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import asyncio


class SecuritiesCrawlerService:
    """증권사 사이트 크롤링 서비스"""

    def __init__(self):
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def search_analyst_reports(
        self,
        analyst_name: str,
        securities_firm: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """애널리스트 리포트 검색 (여러 증권사 사이트 크롤링)"""
        results = []
        
        # 주요 증권사 사이트 목록
        securities_sites = [
            {
                "name": "미래에셋증권",
                "url": "https://securities.miraeasset.com",
                "search_path": "/research/report"
            },
            {
                "name": "KB증권",
                "url": "https://www.kbsec.com",
                "search_path": "/research/report"
            },
            {
                "name": "NH투자증권",
                "url": "https://www.nhqv.com",
                "search_path": "/research/report"
            },
            {
                "name": "삼성증권",
                "url": "https://www.samsungpop.com",
                "search_path": "/research/report"
            },
            {
                "name": "한국투자증권",
                "url": "https://www.truefriend.com",
                "search_path": "/research/report"
            },
        ]

        # 각 증권사 사이트에서 검색
        tasks = []
        for site in securities_sites:
            if securities_firm in site["name"] or site["name"] in securities_firm:
                tasks.append(self._crawl_securities_site(
                    site, analyst_name, start_date, end_date
                ))

        if tasks:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results_list:
                if isinstance(result, list):
                    results.extend(result)
                elif isinstance(result, Exception):
                    print(f"크롤링 오류: {str(result)}")

        return results

    async def _crawl_securities_site(
        self,
        site: Dict[str, str],
        analyst_name: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """특정 증권사 사이트 크롤링"""
        results = []
        
        try:
            # 검색 URL 구성 (실제 사이트 구조에 맞게 수정 필요)
            search_url = f"{site['url']}{site['search_path']}"
            
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                # 검색 파라미터
                params = {
                    "analyst": analyst_name,
                    "start_date": start_date or "",
                    "end_date": end_date or ""
                }
                
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                # HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 리포트 목록 추출 (실제 사이트 구조에 맞게 수정 필요)
                report_items = soup.find_all('div', class_=re.compile(r'report|item|card', re.I))
                
                for item in report_items[:20]:  # 최대 20개
                    try:
                        report_data = self._extract_report_info(item, site["name"])
                        if report_data:
                            report_data["source_site"] = site["name"]
                            report_data["source_url"] = site["url"]
                            results.append(report_data)
                    except Exception as e:
                        print(f"리포트 추출 오류: {str(e)}")
                        continue

        except Exception as e:
            print(f"{site['name']} 크롤링 오류: {str(e)}")
        
        return results

    def _extract_report_info(self, item, securities_firm: str) -> Optional[Dict[str, Any]]:
        """리포트 정보 추출"""
        try:
            # 제목 추출
            title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|subject', re.I))
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 날짜 추출
            date_elem = item.find(['span', 'div', 'time'], class_=re.compile(r'date|time', re.I))
            date_str = date_elem.get_text(strip=True) if date_elem else ""
            
            # URL 추출
            link_elem = item.find('a', href=True)
            url = link_elem['href'] if link_elem else ""

            # 애널리스트 이름 추출
            analyst_elem = item.find(['span', 'div'], class_=re.compile(r'analyst|author|writer', re.I))
            analyst_name = analyst_elem.get_text(strip=True) if analyst_elem else ""

            if not title:
                return None

            # 날짜 파싱
            publication_date = self._parse_date(date_str)

            return {
                "title": title,
                "analyst_name": analyst_name,
                "securities_firm": securities_firm,
                "publication_date": publication_date.isoformat() if publication_date else None,
                "source_url": url,
                "crawled_at": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"리포트 정보 추출 오류: {str(e)}")
            return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        
        # 다양한 날짜 형식 시도
        date_formats = [
            "%Y-%m-%d",
            "%Y.%m.%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        
        # 상대 날짜 처리 (예: "3일 전", "1주 전")
        if "일 전" in date_str or "주 전" in date_str or "개월 전" in date_str:
            # 간단한 처리: 현재 날짜 반환 (실제로는 계산 필요)
            return datetime.now()
        
        return None

