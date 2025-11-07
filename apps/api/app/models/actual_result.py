"""
Actual Result model
"""
from sqlalchemy import Column, String, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class ActualResult(BaseModel):
    """실제 결과 모델"""
    __tablename__ = "actual_results"

    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)

    actual_value = Column(Numeric(20, 2), nullable=False)
    unit = Column(String(20))
    period = Column(String(20), nullable=False, index=True)
    announcement_date = Column(Date)
    source = Column(String(255))  # 출처
    source_url = Column(Text)
    metadata = Column(JSONB)

    # Relationships
    prediction = relationship("Prediction", back_populates="actual_results")
    company = relationship("Company", back_populates="actual_results")

