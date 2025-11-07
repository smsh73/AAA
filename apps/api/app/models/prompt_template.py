"""
Prompt Template model
"""
from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel


class PromptTemplate(BaseModel):
    """프롬프트 템플릿 모델"""
    __tablename__ = "prompt_templates"

    template_name = Column(String(255), nullable=False, unique=True)
    template_type = Column(String(50), nullable=False, index=True)  # target_price, performance, sns, media
    kpi_type = Column(String(50), index=True)
    prompt_content = Column(Text, nullable=False)
    input_schema = Column(JSONB)
    output_schema = Column(JSONB)
    max_input_tokens = Column(Integer, default=1000000)
    max_output_tokens = Column(Integer, default=100000)
    version = Column(String(20), default="1.0.0")
    is_active = Column(Boolean, default=True, nullable=False, index=True)

