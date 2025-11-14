"""
Reports router
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.report import (
    ReportResponse,
    ReportUploadResponse,
    ExtractionStatusResponse,
    ReportListResponse,
    ReportGroupedResponse,
    ReportDetailResponse,
    CompanyExtractionResponse
)
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """리포트 업로드 및 추출 시작"""
    service = ReportService(db)
    return await service.upload_and_extract(file, analyst_id, company_id, background_tasks)


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


@router.get("", response_model=ReportListResponse)
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """리포트 목록 조회"""
    service = ReportService(db)
    reports = service.get_reports(skip=skip, limit=limit, analyst_id=analyst_id, company_id=company_id, status=status)
    total = service.get_reports_count(analyst_id=analyst_id, company_id=company_id, status=status)
    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """리포트 상세 조회 (N+1 쿼리 최적화)"""
    from app.models.prediction import Prediction
    from app.models.report import Report
    
    # Eager loading으로 company 관계를 한 번에 로드
    report = db.query(Report).options(
        joinedload(Report.company)
    ).filter(Report.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # 리포트 상세 정보 구성
    report_dict = {
        "id": report.id,
        "analyst_id": report.analyst_id,
        "company_id": report.company_id,
        "title": report.title,
        "publication_date": report.publication_date,
        "report_type": report.report_type,
        "file_path": report.file_path,
        "file_size": report.file_size,
        "total_pages": None,  # TODO: 페이지 수 계산
        "status": report.status,
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }
    
    # 이미 로드된 company 관계 사용 (추가 쿼리 없음)
    company = report.company if hasattr(report, 'company') else None
    report_dict["extracted_company_name"] = company.name_kr if company else None
    
    # 추출된 예측 정보 개수 (count 쿼리는 빠름)
    predictions_count = db.query(Prediction).filter(Prediction.report_id == report_id).count()
    report_dict["predictions_count"] = predictions_count
    
    return ReportDetailResponse(**report_dict)


@router.get("/grouped", response_model=ReportGroupedResponse)
async def get_reports_grouped(
    period: Optional[str] = None,
    analyst_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """기간별 그룹화된 리포트 조회 (기간>애널리스트>리포트)"""
    service = ReportService(db)
    result = service.get_reports_grouped_by_period(period=period, analyst_id=analyst_id)
    return ReportGroupedResponse(**result)


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


@router.get("/{report_id}/extracted-company", response_model=CompanyExtractionResponse)
async def get_extracted_company(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """추출된 기업 정보 조회"""
    service = ReportService(db)
    company_info = service.get_extracted_company_info(report_id)
    if not company_info:
        return CompanyExtractionResponse(
            company_id=None,
            company_name=None,
            ticker=None,
            confidence=None,
            message="기업 정보가 추출되지 않았습니다."
        )
    return CompanyExtractionResponse(
        company_id=UUID(company_info["company_id"]),
        company_name=company_info["company_name"],
        ticker=company_info["ticker"],
        confidence="high",
        message="기업 정보가 자동으로 추출되었습니다."
    )

