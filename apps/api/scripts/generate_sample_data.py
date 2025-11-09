"""
샘플 데이터 생성 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.analyst import Analyst
from app.models.company import Company
from app.models.report import Report
from app.models.evaluation import Evaluation
from app.models.scorecard import Scorecard
from app.models.award import Award
from uuid import uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal


def create_sample_data():
    """샘플 데이터 생성"""
    db: Session = SessionLocal()
    
    try:
        # 샘플 애널리스트 생성
        analysts = []
        firms = ["삼성증권", "KB증권", "미래에셋증권", "NH투자증권", "한국투자증권"]
        sectors = ["반도체", "자동차", "방산", "금융", "바이오"]
        
        for i in range(10):
            analyst = Analyst(
                id=uuid4(),
                name=f"애널리스트 {i+1}",
                firm=firms[i % len(firms)],
                department="리서치센터",
                sector=sectors[i % len(sectors)],
                experience_years=5 + (i % 10),
                email=f"analyst{i+1}@example.com"
            )
            db.add(analyst)
            analysts.append(analyst)
        
        db.commit()
        print(f"✅ {len(analysts)}명의 애널리스트 생성 완료")
        
        # 샘플 기업 생성
        companies = []
        company_names = [
            ("삼성전자", "005930"),
            ("SK하이닉스", "000660"),
            ("현대자동차", "005380"),
            ("LG전자", "066570"),
            ("NAVER", "035420")
        ]
        
        for name_kr, ticker in company_names:
            company = Company(
                id=uuid4(),
                ticker=ticker,  # ticker는 nullable이지만 샘플 데이터에는 포함
                name_kr=name_kr,
                name_en=name_kr,
                sector="IT",
                market_cap=Decimal("1000000000000")
            )
            db.add(company)
            companies.append(company)
        
        db.commit()
        print(f"✅ {len(companies)}개의 기업 생성 완료")
        
        # 샘플 리포트 생성
        reports = []
        for i in range(20):
            report = Report(
                id=uuid4(),
                analyst_id=analysts[i % len(analysts)].id,
                company_id=companies[i % len(companies)].id if i % 2 == 0 else None,
                title=f"리포트 제목 {i+1}",
                publication_date=date.today() - timedelta(days=i),
                status="completed"
            )
            db.add(report)
            reports.append(report)
        
        db.commit()
        print(f"✅ {len(reports)}개의 리포트 생성 완료")
        
        # 샘플 평가 생성
        evaluations = []
        for i, report in enumerate(reports[:10]):
            evaluation = Evaluation(
                id=uuid4(),
                report_id=report.id,
                analyst_id=report.analyst_id,
                company_id=report.company_id,
                evaluation_period=f"2025-Q{(i % 4) + 1}",
                evaluation_date=date.today() - timedelta(days=i),
                final_score=Decimal("75.5") + Decimal(str(i)),
                status="completed"
            )
            db.add(evaluation)
            evaluations.append(evaluation)
        
        db.commit()
        print(f"✅ {len(evaluations)}개의 평가 생성 완료")
        
        # 샘플 스코어카드 생성
        scorecards = []
        for i, evaluation in enumerate(evaluations):
            scorecard = Scorecard(
                id=uuid4(),
                analyst_id=evaluation.analyst_id,
                company_id=evaluation.company_id,
                period=evaluation.evaluation_period,
                final_score=evaluation.final_score,
                ranking=i+1,
                scorecard_data={
                    "evaluation_id": str(evaluation.id),
                    "scores": {
                        "accuracy": 80.0 + i,
                        "timeliness": 75.0 + i,
                        "coverage": 70.0 + i
                    }
                }
            )
            db.add(scorecard)
            scorecards.append(scorecard)
        
        db.commit()
        print(f"✅ {len(scorecards)}개의 스코어카드 생성 완료")
        
        # 샘플 어워드 생성
        awards = []
        award_types = ["gold", "silver", "bronze"]
        categories = ["반도체", "자동차", "방산", "금융", "바이오"]
        
        for i in range(15):
            award = Award(
                id=uuid4(),
                analyst_id=analysts[i % len(analysts)].id,
                award_type=award_types[i % len(award_types)],
                award_category=categories[i % len(categories)],
                period="2025-Q1",
                rank=i+1
            )
            db.add(award)
            awards.append(award)
        
        db.commit()
        print(f"✅ {len(awards)}개의 어워드 생성 완료")
        
        print("\n🎉 샘플 데이터 생성 완료!")
        print(f"  - 애널리스트: {len(analysts)}명")
        print(f"  - 기업: {len(companies)}개")
        print(f"  - 리포트: {len(reports)}개")
        print(f"  - 평가: {len(evaluations)}개")
        print(f"  - 스코어카드: {len(scorecards)}개")
        print(f"  - 어워드: {len(awards)}개")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()

