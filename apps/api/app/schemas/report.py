"""
Report schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date


class ReportUploadResponse(BaseModel):
    report_id: UUID
    status: str
    estimated_completion_time: Optional[datetime] = None


class ExtractionStatusResponse(BaseModel):
    report_id: UUID
    status: str
    progress: dict
    estimated_completion_time: Optional[datetime] = None


class PredictionResponse(BaseModel):
    id: UUID
    prediction_type: str
    predicted_value: float
    unit: Optional[str] = None
    period: Optional[str] = None


class ReportResponse(BaseModel):
    id: UUID
    analyst_id: UUID
    company_id: Optional[UUID] = None
    title: str
    publication_date: date
    report_type: Optional[str] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    skip: int
    limit: int


class ReportGroupedResponse(BaseModel):
    """기간별 그룹화된 리포트 응답"""
    periods: List[Dict[str, Any]]
    total: int


class ReportDetailResponse(ReportResponse):
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    total_pages: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime
