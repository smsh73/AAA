"""
Report models
"""
from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel


class Report(BaseModel):
    """리포트 모델"""
    __tablename__ = "reports"

    analyst_id = Column(UUID(as_uuid=True), ForeignKey("analysts.id"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), index=True)
    market_id = Column(UUID(as_uuid=True), ForeignKey("markets.id"), index=True)

    title = Column(String(500), nullable=False)
    report_type = Column(String(50))  # 주식, 산업, 이슈전략 등
    publication_date = Column(Date, nullable=False, index=True)
    source_url = Column(Text)
    file_path = Column(Text)  # PDF 파일 경로
    file_size = Column(Integer)  # 파일 크기 (bytes)
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed

    # Extracted content
    parsed_json = Column(JSONB)  # 파싱된 JSON 데이터
    extracted_texts = relationship("ExtractedText", back_populates="report")
    extracted_tables = relationship("ExtractedTable", back_populates="report")
    extracted_images = relationship("ExtractedImage", back_populates="report")

    # Relationships
    analyst = relationship("Analyst", back_populates="reports")
    company = relationship("Company", back_populates="reports")
    market = relationship("Market", back_populates="reports")
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="report")


class ReportSection(BaseModel):
    """리포트 섹션 모델"""
    __tablename__ = "report_sections"

    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    section_type = Column(String(50))  # summary, analysis, forecast 등
    title = Column(String(500))
    content = Column(Text)
    page_number = Column(Integer)
    order = Column(Integer)

    # Relationships
    report = relationship("Report", back_populates="sections")


class ExtractedText(BaseModel):
    """추출된 텍스트 모델"""
    __tablename__ = "extracted_texts"

    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    bbox = Column(JSONB)  # bounding box [x, y, width, height]
    confidence = Column(String(10))  # high, medium, low
    language = Column(String(10))  # ko, en

    report = relationship("Report", back_populates="extracted_texts")


class ExtractedTable(BaseModel):
    """추출된 표 모델"""
    __tablename__ = "extracted_tables"

    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    table_data = Column(JSONB, nullable=False)  # 표 데이터 (2D 배열)
    bbox = Column(JSONB)
    confidence = Column(String(10))

    report = relationship("Report", back_populates="extracted_tables")


class ExtractedImage(BaseModel):
    """추출된 이미지 모델"""
    __tablename__ = "extracted_images"

    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    image_path = Column(Text, nullable=False)
    image_type = Column(String(50))  # chart, graph, diagram 등
    bbox = Column(JSONB)
    analysis_result = Column(JSONB)  # VLM 분석 결과

    report = relationship("Report", back_populates="extracted_images")

