"""
Collection Job model - 데이터 수집 작업 추적 모델
"""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class CollectionJob(BaseModel):
    """데이터 수집 작업 추적 모델"""
    __tablename__ = "collection_jobs"

    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    collection_types = Column(ARRAY(String), nullable=False)  # ["target_price", "performance", "sns", "media"]
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(String(20), nullable=False, index=True, default="pending")  # pending, running, completed, failed
    progress = Column(JSONB, default={})  # {"target_price": {"total": 10, "completed": 5}, ...}
    overall_progress = Column(String(10), default="0.0")  # 전체 진행률 (0.0 ~ 100.0)
    
    estimated_completion_time = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(String(500))
    
    # Relationships
    analyst = relationship("Analyst", back_populates="collection_jobs")
    logs = relationship("DataCollectionLog", back_populates="collection_job", cascade="all, delete-orphan")

