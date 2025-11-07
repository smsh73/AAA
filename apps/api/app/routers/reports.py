"""
Reports router
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.report import ReportResponse, ReportUploadResponse, ExtractionStatusResponse
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """리포트 업로드 및 추출 시작"""
    service = ReportService(db)
    return await service.upload_and_extract(file, analyst_id, company_id)


@router.get("/{report_id}/extraction-status", response_model=ExtractionStatusResponse)
async def get_extraction_status(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """추출 상태 조회"""
    service = ReportService(db)
    status = service.get_extraction_status(report_id)
    if not status:
        raise HTTPException(status_code=404, detail="Report not found")
    return status


@router.get("/{report_id}/predictions")
async def get_predictions(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """예측 정보 조회"""
    service = ReportService(db)
    predictions = service.get_predictions(report_id)
    if predictions is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "predictions": predictions}

