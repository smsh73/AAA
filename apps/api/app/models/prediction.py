"""
Prediction model
"""
from sqlalchemy import Column, String, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Prediction(BaseModel):
    """예측 정보 모델"""
    __tablename__ = "predictions"

    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), index=True)

    prediction_type = Column(String(50), nullable=False, index=True)  # target_price, revenue, operating_profit 등
    predicted_value = Column(Numeric(20, 2), nullable=False)
    unit = Column(String(20))  # 원, 억원, % 등
    period = Column(String(20))  # 2025Q1, 2025-06 등
    reasoning = Column(Text)  # 예측 근거
    confidence = Column(String(10))  # high, medium, low
    metadata = Column(JSONB)

    # Relationships
    report = relationship("Report", back_populates="predictions")
    company = relationship("Company", back_populates="predictions")
    market = relationship("Market", back_populates="predictions")
    actual_results = relationship("ActualResult", back_populates="prediction")

