"""
데이터베이스 초기화 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, Base
from app.models import (
    Analyst, Company, Market, Report, ReportSection, ExtractedText, ExtractedTable,
    ExtractedImage, Prediction, ActualResult, Evaluation, EvaluationScore,
    Scorecard, Award, DataSource, DataCollectionLog, CollectionJob,
    EvaluationReport, PromptTemplate
)


def init_db():
    """데이터베이스 초기화"""
    print("데이터베이스 테이블 생성 중...")
    Base.metadata.create_all(bind=engine)
    print("데이터베이스 초기화 완료!")


if __name__ == "__main__":
    init_db()

