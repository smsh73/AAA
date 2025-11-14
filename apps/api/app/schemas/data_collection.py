"""
Data collection schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date


class DataCollectionStartRequest(BaseModel):
    analyst_id: UUID
    collection_types: List[str]  # target_price, performance, sns, media
    start_date: date
    end_date: date


class DataCollectionStartResponse(BaseModel):
    collection_job_id: UUID
    status: str
    estimated_completion_time: Optional[datetime] = None


class DataCollectionStatusResponse(BaseModel):
    collection_job_id: UUID
    status: str
    progress: Dict[str, Any]
    overall_progress: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DataCollectionLogResponse(BaseModel):
    id: UUID
    analyst_id: UUID
    company_id: Optional[UUID] = None
    collection_job_id: Optional[UUID] = None
    collection_type: str
    prompt_template_id: Optional[str] = None
    perplexity_request: Optional[Dict[str, Any]] = None
    perplexity_response: Optional[Dict[str, Any]] = None
    collected_data: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    log_message: Optional[str] = None  # 실시간 로그 메시지
    collection_time: Optional[float] = None
    token_usage: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

