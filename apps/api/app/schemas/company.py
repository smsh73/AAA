"""
Company schemas
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CompanyResponse(BaseModel):
    id: UUID
    ticker: str
    name_kr: str
    name_en: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None

    class Config:
        from_attributes = True

