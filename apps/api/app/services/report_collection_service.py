"""
리포트 수집 및 저장 서비스
"""
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import httpx
import aiofiles
import os

from app.models.report import Report
from app.models.analyst import Analyst
from app.models.company import Company
from app.models.data_collection_log import DataCollectionLog
from app.services.securities_crawler_service import SecuritiesCrawlerService
from app.services.google_search_service import GoogleSearchService
from app.services.report_service import ReportService


class ReportCollectionService:
    """리포트 수집 및 저장 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.securities_crawler = SecuritiesCrawlerService()
        self.google_search = GoogleSearchService()
        self.report_service = ReportService(db)
        self.storage_path = os.getenv("STORAGE_PATH", "/app/storage/reports")

    async def collect_and_save_reports(
        self,
        analyst_id: UUID,
        collection_job_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """애널리스트 리포트 수집 및 저장"""
        analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
        if not analyst:
            raise ValueError(f"Analyst not found: {analyst_id}")

        results = {
            "securities_crawled": 0,
            "google_searched": 0,
            "reports_saved": 0,
            "reports_failed": 0,
            "reports": []
        }

        # 1. 증권사 사이트 크롤링
        try:
            securities_reports = await self.securities_crawler.search_analyst_reports(
                analyst_name=analyst.name,
                securities_firm=analyst.firm,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )
            results["securities_crawled"] = len(securities_reports)

            # 리포트 저장
            for report_data in securities_reports:
                try:
                    saved_report = await self._save_report_from_data(
                        report_data, analyst_id, collection_job_id, "securities_crawl"
                    )
                    if saved_report:
                        results["reports_saved"] += 1
                        results["reports"].append(saved_report)
                    else:
                        results["reports_failed"] += 1
                except Exception as e:
                    print(f"리포트 저장 오류: {str(e)}")
                    results["reports_failed"] += 1
        except Exception as e:
            print(f"증권사 크롤링 오류: {str(e)}")

        # 2. 구글 검색
        try:
            google_reports = await self.google_search.search_analyst_reports(
                analyst_name=analyst.name,
                securities_firm=analyst.firm,
                start_date=start_date.isoformat() if start_date else None,
                end_date=end_date.isoformat() if end_date else None
            )
            results["google_searched"] = len(google_reports)

            # 리포트 저장
            for report_data in google_reports:
                try:
                    saved_report = await self._save_report_from_data(
                        report_data, analyst_id, collection_job_id, "google_search"
                    )
                    if saved_report:
                        results["reports_saved"] += 1
                        results["reports"].append(saved_report)
                    else:
                        results["reports_failed"] += 1
                except Exception as e:
                    print(f"리포트 저장 오류: {str(e)}")
                    results["reports_failed"] += 1
        except Exception as e:
            print(f"구글 검색 오류: {str(e)}")

        return results

    async def _save_report_from_data(
        self,
        report_data: Dict[str, Any],
        analyst_id: UUID,
        collection_job_id: Optional[UUID],
        source: str
    ) -> Optional[Dict[str, Any]]:
        """수집된 리포트 데이터를 DB에 저장"""
        try:
            # 중복 체크 (URL 기준)
            source_url = report_data.get("link") or report_data.get("source_url")
            if source_url:
                existing = self.db.query(Report).filter(
                    Report.source_url == source_url,
                    Report.analyst_id == analyst_id
                ).first()
                if existing:
                    return None  # 이미 존재하는 리포트

            # 리포트 생성
            report = Report(
                analyst_id=analyst_id,
                title=report_data.get("title", ""),
                report_type="주식",  # 기본값
                publication_date=self._parse_date(report_data.get("publication_date")),
                source_url=source_url,
                status="pending"
            )

            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            # 로그 저장
            log = DataCollectionLog(
                analyst_id=analyst_id,
                collection_job_id=collection_job_id,
                collection_type=f"report_collection_{source}",
                collected_data={
                    "report_id": str(report.id),
                    "title": report.title,
                    "source": source,
                    "source_url": source_url
                },
                status="success"
            )
            self.db.add(log)
            self.db.commit()

            # PDF 다운로드 시도 (URL이 있는 경우)
            if source_url and source_url.endswith(".pdf"):
                try:
                    await self._download_pdf(report.id, source_url)
                except Exception as e:
                    print(f"PDF 다운로드 오류: {str(e)}")

            return {
                "id": str(report.id),
                "title": report.title,
                "source": source,
                "publication_date": report.publication_date.isoformat() if report.publication_date else None
            }
        except Exception as e:
            print(f"리포트 저장 오류: {str(e)}")
            self.db.rollback()
            return None

    async def _download_pdf(self, report_id: UUID, url: str) -> Optional[str]:
        """PDF 파일 다운로드"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                # 파일 저장
                os.makedirs(self.storage_path, exist_ok=True)
                file_path = os.path.join(self.storage_path, f"{report_id}.pdf")

                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(response.content)

                # 리포트에 파일 경로 저장
                report = self.db.query(Report).filter(Report.id == report_id).first()
                if report:
                    report.file_path = file_path
                    report.file_size = len(response.content)
                    self.db.commit()

                return file_path
        except Exception as e:
            print(f"PDF 다운로드 오류: {str(e)}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        try:
            if isinstance(date_str, str):
                # ISO 형식
                if "T" in date_str:
                    return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
                # YYYY-MM-DD 형식
                return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass

        return None

