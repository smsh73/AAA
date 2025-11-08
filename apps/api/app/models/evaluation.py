"""
Evaluation models
"""
from sqlalchemy import Column, String, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Evaluation(BaseModel):
    """평가 모델"""
    __tablename__ = "evaluations"

    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), index=True)

    evaluation_period = Column(String(20), nullable=False, index=True)  # 2025-Q1
    evaluation_date = Column(Date, nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    
    final_score = Column(Numeric(10, 2))  # 최종 점수
    ai_quantitative_score = Column(Numeric(10, 2))  # AI 정량 분석 점수
    sns_market_score = Column(Numeric(10, 2))  # SNS·시장 반응 점수
    expert_survey_score = Column(Numeric(10, 2))  # 전문가 평가 및 설문 점수
    
    metadata = Column(JSONB)

    # Relationships
    analyst = relationship("Analyst", back_populates="evaluations")
    company = relationship("Company", back_populates="evaluations")
    scores = relationship("EvaluationScore", back_populates="evaluation", cascade="all, delete-orphan")
    evaluation_report = relationship("EvaluationReport", back_populates="evaluation", uselist=False)


class EvaluationScore(BaseModel):
    """평가 점수 모델"""
    __tablename__ = "evaluation_scores"

    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=False, index=True)

    score_type = Column(String(50), nullable=False, index=True)  # target_price_accuracy, performance_accuracy 등
    score_value = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(5, 4))  # 가중치
    details = Column(JSONB)  # 상세 점수 정보
    reasoning = Column(Text)  # 점수 산출 근거

    # Relationships
    evaluation = relationship("Evaluation", back_populates="scores")

