"""
Evaluation reports router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.evaluation_report import (
    EvaluationReportGenerateRequest,
    EvaluationReportGenerateResponse,
    EvaluationReportResponse
)
from app.services.evaluation_report_service import EvaluationReportService

router = APIRouter()


@router.post("/generate", response_model=EvaluationReportGenerateResponse)
async def generate_report(
    request: EvaluationReportGenerateRequest,
    db: Session = Depends(get_db)
):
    """상세 평가보고서 생성"""
    service = EvaluationReportService(db)
    return await service.generate_report(
        evaluation_id=request.evaluation_id,
        include_sections=request.include_sections,
        detail_level=request.detail_level
    )


@router.get("/{report_id}", response_model=EvaluationReportResponse)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """상세 평가보고서 조회"""
    service = EvaluationReportService(db)
    report = service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

