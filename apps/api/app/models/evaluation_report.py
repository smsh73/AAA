"""
Evaluation Report model
"""
from sqlalchemy import Column, String, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class EvaluationReport(BaseModel):
    """상세 평가보고서 모델"""
    __tablename__ = "evaluation_reports"

    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=False, unique=True, index=True)
    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)

    report_type = Column(String(50), default="detailed_evaluation")
    report_structure = Column(JSONB)
    report_content = Column(JSONB)
    report_summary = Column(Text)
    data_sources_count = Column(Integer, default=0)
    verification_status = Column(String(20), default="pending")  # pending, verified, failed
    report_quality_score = Column(Numeric(5, 4))
    generated_by = Column(JSONB)  # 생성에 참여한 LLM 목록

    # Relationships
    evaluation = relationship("Evaluation", back_populates="evaluation_report")

