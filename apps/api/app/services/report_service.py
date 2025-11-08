"""
Report service
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import os
import aiofiles
from pathlib import Path

from app.models.report import Report
from app.schemas.report import ReportUploadResponse, ExtractionStatusResponse
from app.services.document_extraction_service import DocumentExtractionService
from app.tasks.report_tasks import parse_report_task
from fastapi import UploadFile


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
        company_id: Optional[UUID] = None
    ) -> ReportUploadResponse:
        """리포트 업로드 및 추출 시작"""
        report_id = uuid4()

        # 파일 저장
        file_path = self.storage_path / "reports" / f"{report_id}.pdf"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 리포트 레코드 생성
        report = Report(
            id=report_id,
            analyst_id=analyst_id,
            company_id=company_id,
            title=file.filename or "Untitled",
            publication_date=datetime.now().date(),
            file_path=str(file_path),
            file_size=len(content),
            status="processing"
        )
        self.db.add(report)
        self.db.commit()

        # 비동기 추출 시작 (Celery 작업으로 실행)
        parse_report_task.delay(str(report_id), str(file_path))

        return ReportUploadResponse(
            report_id=report_id,
            status="processing",
            estimated_completion_time=datetime.utcnow() + timedelta(minutes=10)
        )

    def get_extraction_status(self, report_id: UUID) -> Optional[ExtractionStatusResponse]:
        """추출 상태 조회"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None

        return ExtractionStatusResponse(
            report_id=report_id,
            status=report.status or "processing",
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

