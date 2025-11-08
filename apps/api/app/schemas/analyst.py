"""
Analyst schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class AnalystBase(BaseModel):
    name: str
    firm: str
    department: Optional[str] = None
    sector: Optional[str] = None
    experience_years: Optional[int] = None
    email: Optional[EmailStr] = None
    profile_url: Optional[str] = None
    bio: Optional[str] = None


class AnalystCreate(AnalystBase):
    pass


class AnalystResponse(AnalystBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalystBulkImportResponse(BaseModel):
    import_id: UUID
    total_records: int
    success_count: int
    failed_count: int
    failed_records: List[dict]
    status: str
    data_collection_started: bool

