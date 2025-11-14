"""
테스트 픽스처 설정
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, date

from app.database import Base, get_db
from app.models.analyst import Analyst
from app.models.company import Company
from app.models.report import Report
from app.models.evaluation import Evaluation, EvaluationScore
from app.models.scorecard import Scorecard
from app.models.award import Award
from app.models.market import Market


# 테스트용 인메모리 SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """테스트용 데이터베이스 세션"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_analyst(db_session: Session):
    """샘플 애널리스트"""
    analyst = Analyst(
        id=uuid4(),
        name="테스트 애널리스트",
        firm="테스트 증권사",
        sector="AI",
        department="IT팀"
    )
    db_session.add(analyst)
    db_session.commit()
    db_session.refresh(analyst)
    return analyst


@pytest.fixture
def sample_company(db_session: Session):
    """샘플 기업"""
    company = Company(
        id=uuid4(),
        name_kr="테스트 기업",
        name_en="Test Company",
        ticker="123456",
        sector="AI"
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture
def sample_market(db_session: Session):
    """샘플 시장"""
    market = Market(
        id=uuid4(),
        name="코스피",
        region="한국"
    )
    db_session.add(market)
    db_session.commit()
    db_session.refresh(market)
    return market


@pytest.fixture
def sample_report(db_session: Session, sample_analyst, sample_company):
    """샘플 리포트"""
    report = Report(
        id=uuid4(),
        analyst_id=sample_analyst.id,
        company_id=sample_company.id,
        title="테스트 리포트",
        publication_date=date.today(),
        status="parsed"
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture
def sample_evaluation(db_session: Session, sample_analyst, sample_company, sample_report):
    """샘플 평가"""
    evaluation = Evaluation(
        id=uuid4(),
        analyst_id=sample_analyst.id,
        company_id=sample_company.id,
        report_id=sample_report.id,
        evaluation_period="2025-Q1",
        evaluation_date=date.today(),
        status="completed",
        final_score=Decimal("85.50")
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)
    return evaluation


@pytest.fixture
def sample_evaluation_scores(db_session: Session, sample_evaluation):
    """샘플 평가 점수"""
    scores = [
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="target_price_accuracy",
            score_value=Decimal("80.0"),
            weight=Decimal("0.25")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="performance_accuracy",
            score_value=Decimal("85.0"),
            weight=Decimal("0.30")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="investment_logic_validity",
            score_value=Decimal("75.0"),
            weight=Decimal("0.15")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="risk_analysis_appropriateness",
            score_value=Decimal("70.0"),
            weight=Decimal("0.10")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="report_frequency",
            score_value=Decimal("90.0"),
            weight=Decimal("0.05")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="sns_attention",
            score_value=Decimal("65.0"),
            weight=Decimal("0.10")
        ),
        EvaluationScore(
            id=uuid4(),
            evaluation_id=sample_evaluation.id,
            score_type="media_frequency",
            score_value=Decimal("60.0"),
            weight=Decimal("0.05")
        ),
    ]
    for score in scores:
        db_session.add(score)
    db_session.commit()
    return scores


@pytest.fixture
def sample_scorecard(db_session: Session, sample_analyst, sample_company):
    """샘플 스코어카드"""
    scorecard = Scorecard(
        id=uuid4(),
        analyst_id=sample_analyst.id,
        company_id=sample_company.id,
        period="2025-Q1",
        final_score=Decimal("85.50"),
        ranking=1,
        scorecard_data={
            "evaluation_id": str(uuid4()),
            "scores": {
                "target_price_accuracy": 80.0,
                "performance_accuracy": 85.0,
            }
        }
    )
    db_session.add(scorecard)
    db_session.commit()
    db_session.refresh(scorecard)
    return scorecard

