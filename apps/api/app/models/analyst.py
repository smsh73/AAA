"""
Analyst model
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Analyst(BaseModel):
    """애널리스트 모델"""
    __tablename__ = "analysts"

    name = Column(String(255), nullable=False, index=True)
    firm = Column(String(255), nullable=False)  # 증권사명
    department = Column(String(255))  # 부서
    sector = Column(String(100))  # 섹터 (반도체, 자동차, 방산, 금융 등)
    experience_years = Column(Integer)
    email = Column(String(255))
    profile_url = Column(Text)
    bio = Column(Text)

    # Relationships
    reports = relationship("Report", back_populates="analyst")
    evaluations = relationship("Evaluation", back_populates="analyst")
    scorecards = relationship("Scorecard", back_populates="analyst")
    awards = relationship("Award", back_populates="analyst")
    data_collection_logs = relationship("DataCollectionLog", back_populates="analyst")

