"""
Market model
"""
from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class Market(BaseModel):
    """시장 모델"""
    __tablename__ = "markets"

    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    region = Column(String(100))  # 지역 (한국, 미국 등)

    # Relationships
    reports = relationship("Report", back_populates="market")
    predictions = relationship("Prediction", back_populates="market")
    scorecards = relationship("Scorecard", back_populates="market")

