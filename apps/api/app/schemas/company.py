"""
Company schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompanyResponse(BaseModel):
    id: UUID
    ticker: Optional[str] = None
    name_kr: Optional[str] = None
    name_en: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    fundamentals: Optional[dict] = None

    class Config:
        from_attributes = True

