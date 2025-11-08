"""
Data Collection Log model
"""
from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class DataCollectionLog(BaseModel):
    """데이터 수집 이력 모델"""
    __tablename__ = "data_collection_logs"

    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    collection_job_id = Column(UUID(as_uuid=True), ForeignKey("collection_jobs.id"), index=True)

    collection_type = Column(String(50), nullable=False, index=True)  # target_price, performance, sns, media
    prompt_template_id = Column(String(100))
    perplexity_request = Column(JSONB)
    perplexity_response = Column(JSONB)
    collected_data = Column(JSONB)
    status = Column(String(20), nullable=False, index=True)  # success, failed, partial
    error_message = Column(Text)
    collection_time = Column(Float)  # 소요 시간 (초)
    token_usage = Column(JSONB)

    # Relationships
    analyst = relationship("Analyst", back_populates="data_collection_logs")
    company = relationship("Company", back_populates="data_collection_logs")
    collection_job = relationship("CollectionJob", back_populates="logs")

