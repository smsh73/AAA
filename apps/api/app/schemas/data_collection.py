"""
Data collection schemas
"""
from pydantic import BaseModel
from typing import List, Optional
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
    progress: dict
    overall_progress: float

