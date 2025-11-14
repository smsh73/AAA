"""
Report service
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import os
import aiofiles
from pathlib import Path

from app.models.report import Report
from app.models.enums import ReportStatus
from app.schemas.report import ReportUploadResponse, ExtractionStatusResponse
from app.services.document_extraction_service import DocumentExtractionService
from app.database import SessionLocal
from fastapi import UploadFile, BackgroundTasks
import asyncio
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """리포트 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.extraction_service = DocumentExtractionService()
        self.storage_path = Path(os.getenv("STORAGE_PATH", "/app/storage"))

    async def upload_and_extract(
        self,
        file: UploadFile,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> ReportUploadResponse:
        """리포트 업로드 및 추출 시작"""
        # 정합성 검증
        if analyst_id:
            from app.models.analyst import Analyst
            analyst = self.db.query(Analyst).filter(Analyst.id == analyst_id).first()
            if not analyst:
                raise ValueError(f"Analyst {analyst_id} not found")
        
        if company_id:
            from app.models.company import Company
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError(f"Company {company_id} not found")
            
            # 애널리스트-기업 섹터 매칭 검증
            if analyst_id and analyst:
                if analyst.sector and company.sector:
                    if analyst.sector != company.sector:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(
                            f"섹터 불일치: 애널리스트 섹터({analyst.sector}) != 기업 섹터({company.sector})"
                        )
        
        report_id = uuid4()

        # 파일 저장
        file_path = self.storage_path / "reports" / f"{report_id}.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 파일명 인코딩 처리 (한글 파일명 지원)
        filename = file.filename or "Untitled"
        if isinstance(filename, bytes):
            try:
                filename = filename.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    filename = filename.decode('cp949')
                except UnicodeDecodeError:
                    filename = filename.decode('latin-1', errors='replace')
        
        # 리포트 레코드 생성
        report = Report(
            id=report_id,
            analyst_id=analyst_id,
            company_id=company_id,
            title=filename,
            publication_date=datetime.now().date(),
            file_path=str(file_path),
            file_size=len(content),
            status=ReportStatus.PROCESSING.value
        )
        self.db.add(report)
        self.db.commit()

        # BackgroundTasks로 비동기 파싱 시작
        if background_tasks:
            background_tasks.add_task(
                self._parse_report_background,
                str(report_id),
                str(file_path)
            )
        else:
            # BackgroundTasks가 없으면 Celery 시도, 실패 시 동기 실행
            try:
                from app.tasks.report_tasks import parse_report_task
                parse_report_task.delay(str(report_id), str(file_path))
            except Exception as e:
                logger.warning(f"Celery 작업 시작 실패, 동기 실행으로 전환: {str(e)}")
                # 동기적으로 파싱 실행
                try:
                    from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
                    
                    # 새 DB 세션 생성 (세션 충돌 방지)
                    db = SessionLocal()
                    try:
                        agent = ReportParsingAgent(db)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(agent.parse_report(report_id, str(file_path)))
                        finally:
                            loop.close()
                    finally:
                        db.close()
                except Exception as parse_error:
                    logger.error(f"리포트 파싱 실패: {str(parse_error)}")
                    report.status = ReportStatus.FAILED.value
                    self.db.commit()

        return ReportUploadResponse(
            report_id=report_id,
            status=ReportStatus.PROCESSING.value,
            estimated_completion_time=datetime.utcnow() + timedelta(minutes=10)
        )
    
    def _parse_report_background(self, report_id_str: str, file_path: str):
        """BackgroundTasks에서 실행되는 리포트 파싱 함수"""
        from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
        from uuid import UUID
        
        # 새 DB 세션 생성 (세션 충돌 방지)
        db = SessionLocal()
        try:
            agent = ReportParsingAgent(db)
            report_id = UUID(report_id_str)
            
            # 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(agent.parse_report(report_id, file_path))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"리포트 파싱 실패 (background): {str(e)}")
            # 리포트 상태를 실패로 업데이트
            try:
                report = db.query(Report).filter(Report.id == UUID(report_id_str)).first()
                if report:
                    report.status = ReportStatus.FAILED.value
                    db.commit()
            except Exception as update_error:
                logger.error(f"리포트 상태 업데이트 실패: {str(update_error)}")
        finally:
            db.close()

    def get_extraction_status(self, report_id: UUID) -> Optional[ExtractionStatusResponse]:
        """추출 상태 조회"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None

        return ExtractionStatusResponse(
            report_id=report_id,
            status=report.status or ReportStatus.PROCESSING.value,
            progress={
                "pages_processed": 0,
                "total_pages": 0,
                "percentage": 0
            },
            estimated_completion_time=None
        )

    def get_reports(
        self,
        skip: int = 0,
        limit: int = 100,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[Report]:
        """리포트 목록 조회"""
        query = self.db.query(Report)

        if analyst_id:
            query = query.filter(Report.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Report.company_id == company_id)
        if status:
            query = query.filter(Report.status == status)

        return query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()

    def get_reports_count(
        self,
        analyst_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> int:
        """리포트 총 개수"""
        query = self.db.query(Report)

        if analyst_id:
            query = query.filter(Report.analyst_id == analyst_id)
        if company_id:
            query = query.filter(Report.company_id == company_id)
        if status:
            query = query.filter(Report.status == status)

        return query.count()

    def get_report(self, report_id: UUID) -> Optional[Report]:
        """리포트 상세 조회"""
        return self.db.query(Report).filter(Report.id == report_id).first()

    def get_extracted_company_info(self, report_id: UUID) -> Optional[Dict[str, Any]]:
        """추출된 기업 정보 조회"""
        from app.models.company import Company
        
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report or not report.company_id:
            return None
        
        company = self.db.query(Company).filter(Company.id == report.company_id).first()
        if not company:
            return None
        
        return {
            "company_id": str(company.id),
            "company_name": company.name_kr,
            "ticker": company.ticker,
            "sector": company.sector
        }

    def get_predictions(self, report_id: UUID):
        """예측 정보 조회"""
        from app.models.prediction import Prediction
        
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None

        predictions = self.db.query(Prediction).filter(
            Prediction.report_id == report_id
        ).all()

        return [
            {
                "id": str(p.id),
                "prediction_type": p.prediction_type,
                "predicted_value": float(p.predicted_value),
                "unit": p.unit,
                "period": p.period,
            }
            for p in predictions
        ]
    
    def get_reports_grouped_by_period(
        self,
        period: Optional[str] = None,
        analyst_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """기간별 그룹화된 리포트 조회 (N+1 쿼리 최적화)"""
        from sqlalchemy.orm import joinedload
        from datetime import datetime, date
        
        # Eager loading으로 analyst 관계를 한 번에 로드
        query = self.db.query(Report).options(
            joinedload(Report.analyst)
        )
        if analyst_id:
            query = query.filter(Report.analyst_id == analyst_id)
        
        reports = query.order_by(Report.publication_date.desc()).all()
        
        # 기간별 그룹화 (발간일 기준으로 분기 계산)
        periods = {}
        
        for report in reports:
            # 발간일 기준으로 기간 계산
            pub_date = report.publication_date
            if not pub_date:
                # 발간일이 없으면 생성일 기준으로 계산
                pub_date = report.created_at.date() if report.created_at else datetime.now().date()
            elif isinstance(pub_date, str):
                pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
            
            quarter = (pub_date.month - 1) // 3 + 1
            period_key = f"{pub_date.year}-Q{quarter}"
            
            # 기간 필터
            if period and period_key != period:
                continue
            
            if period_key not in periods:
                periods[period_key] = {
                    "period": period_key,
                    "analysts": {}
                }
            
            # 애널리스트별 그룹화 (이미 로드된 analyst 사용)
            if report.analyst_id:
                analyst_id_str = str(report.analyst_id)
                if analyst_id_str not in periods[period_key]["analysts"]:
                    # 이미 로드된 analyst 관계 사용 (추가 쿼리 없음)
                    analyst = report.analyst if hasattr(report, 'analyst') else None
                    periods[period_key]["analysts"][analyst_id_str] = {
                        "analyst_id": analyst_id_str,
                        "analyst_name": analyst.name if analyst else "Unknown",
                        "analyst_firm": analyst.firm if analyst else "",
                        "reports": []
                    }
                
                # 리포트 추가
                pub_date_str = ""
                if report.publication_date:
                    if isinstance(report.publication_date, date):
                        pub_date_str = report.publication_date.isoformat()
                    else:
                        pub_date_str = str(report.publication_date)
                elif report.created_at:
                    pub_date_str = report.created_at.date().isoformat()
                
                periods[period_key]["analysts"][analyst_id_str]["reports"].append({
                    "id": str(report.id),
                    "title": report.title or "제목 없음",
                    "publication_date": pub_date_str,
                    "status": report.status or "pending",
                    "company_id": str(report.company_id) if report.company_id else None,
                })
        
        # 딕셔너리를 리스트로 변환
        periods_list = []
        for period_key, period_data in periods.items():
            analysts_list = []
            for analyst_id, analyst_data in period_data["analysts"].items():
                analysts_list.append(analyst_data)
            
            periods_list.append({
                "period": period_key,
                "analysts": analysts_list,
                "total_reports": sum(
                    len(analyst["reports"])
                    for analyst in analysts_list
                )
            })
        
        return {
            "periods": periods_list,
            "total": len(reports)
        }

