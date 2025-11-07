"""
Report schemas
"""
from pydantic import BaseModel
from typing import Optional, List
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

