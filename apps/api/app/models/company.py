"""
Company model
"""
from sqlalchemy import Column, String, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Company(BaseModel):
    """기업 모델"""
    __tablename__ = "companies"

    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name_kr = Column(String(255), nullable=False)
    name_en = Column(String(255))
    sector = Column(String(100))
    market_cap = Column(Numeric(20, 2))  # 시가총액
    fundamentals = Column(JSONB)  # 재무 정보
    metadata = Column(JSONB)  # 추가 메타데이터

    # Relationships
    reports = relationship("Report", back_populates="company")
    predictions = relationship("Prediction", back_populates="company")
    actual_results = relationship("ActualResult", back_populates="company")
    evaluations = relationship("Evaluation", back_populates="company")
    scorecards = relationship("Scorecard", back_populates="company")
    data_collection_logs = relationship("DataCollectionLog", back_populates="company")

