"""
Award model
"""
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Award(BaseModel):
    """수상 내역 모델"""
    __tablename__ = "awards"

    scorecard_id = Column(UUID(as_uuid=True), ForeignKey("scorecards.id"), nullable=False, index=True)
    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)

    award_type = Column(String(20), nullable=False)  # gold, silver, bronze
    award_category = Column(String(50), nullable=False, index=True)  # AI, 2차전지, 방산, IPO 등
    period = Column(String(20), nullable=False, index=True)
    rank = Column(Integer, nullable=False, index=True)

    # Relationships
    scorecard = relationship("Scorecard", back_populates="awards")
    analyst = relationship("Analyst", back_populates="awards")

