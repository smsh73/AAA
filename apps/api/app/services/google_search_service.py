"""
구글 검색 서비스 - 애널리스트 리포트 검색
"""
import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re


class GoogleSearchService:
    """구글 검색 서비스"""

    def __init__(self):
        self.timeout = 30.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Google Custom Search API 사용 (선택적)
        self.google_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")

    async def search_analyst_reports(
        self,
        analyst_name: str,
        securities_firm: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """구글 검색으로 애널리스트 리포트 검색"""
        if self.google_api_key and self.google_cse_id:
            return await self._search_with_api(analyst_name, securities_firm, start_date, end_date)
        else:
            return await self._search_with_scraping(analyst_name, securities_firm, start_date, end_date)

    async def _search_with_api(
        self,
        analyst_name: str,
        securities_firm: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Google Custom Search API 사용"""
        results = []
        
        query = f"{analyst_name} {securities_firm} 애널리스트 리포트"
        if start_date:
            query += f" {start_date}"
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": 10
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "items" in data:
                    for item in data["items"]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "analyst_name": analyst_name,
                            "securities_firm": securities_firm,
                            "source": "google_search",
                            "crawled_at": datetime.now().isoformat()
                        })
        except Exception as e:
            print(f"Google API 검색 오류: {str(e)}")
        
        return results

    async def _search_with_scraping(
        self,
        analyst_name: str,
        securities_firm: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[Dict[str, Any]]:
        """구글 검색 결과 스크래핑 (API 없이)"""
        results = []
        
        query = f"{analyst_name} {securities_firm} 애널리스트 리포트"
        if start_date:
            query += f" {start_date}"
        
        # 구글 검색 URL
        search_url = "https://www.google.com/search"
        params = {
            "q": query,
            "num": 10
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 검색 결과 추출
                search_results = soup.find_all('div', class_=re.compile(r'g|result', re.I))
                
                for result in search_results[:10]:
                    try:
                        # 제목 추출
                        title_elem = result.find('h3')
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        
                        # 링크 추출
                        link_elem = result.find('a', href=True)
                        link = link_elem['href'] if link_elem else ""
                        
                        # 스니펫 추출
                        snippet_elem = result.find(['span', 'div'], class_=re.compile(r'snippet|description', re.I))
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if title and link:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "link": link,
                                "analyst_name": analyst_name,
                                "securities_firm": securities_firm,
                                "source": "google_search",
                                "crawled_at": datetime.now().isoformat()
                            })
                    except Exception as e:
                        print(f"검색 결과 추출 오류: {str(e)}")
                        continue

        except Exception as e:
            print(f"구글 검색 오류: {str(e)}")
        
        return results

