"""
Scorecard model
"""
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Scorecard(BaseModel):
    """스코어카드 모델"""
    __tablename__ = "scorecards"

    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), index=True)

    period = Column(String(20), nullable=False, index=True)  # 2025-Q1
    final_score = Column(Numeric(10, 2), nullable=False, index=True)
    ranking = Column(Integer, index=True)
    scorecard_data = Column(JSONB)  # 스코어카드 상세 데이터

    # Relationships
    analyst = relationship("Analyst", back_populates="scorecards")
    company = relationship("Company", back_populates="scorecards")
    market = relationship("Market", back_populates="scorecards")
    awards = relationship("Award", back_populates="scorecard")

