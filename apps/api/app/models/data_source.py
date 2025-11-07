"""
Data Source model
"""
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from .base import BaseModel


class DataSource(BaseModel):
    """데이터 소스 모델"""
    __tablename__ = "data_sources"

    source_name = Column(String(255), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False, index=True)  # dart, news, sns 등
    source_url = Column(String(500))
    reliability = Column(String(20))  # high, medium, low
    update_frequency = Column(String(50))  # daily, weekly, monthly
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    metadata = Column(JSONB)

