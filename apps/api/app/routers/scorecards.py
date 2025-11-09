"""
Scorecards router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.scorecard import ScorecardResponse, ScorecardDetailResponse, ScorecardRankingResponse
from app.services.scorecard_service import ScorecardService

router = APIRouter()


@router.get("", response_model=List[ScorecardResponse])
async def get_scorecards(
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    market_id: Optional[UUID] = None,
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """스코어카드 조회"""
    service = ScorecardService(db)
    return service.get_scorecards(
        analyst_id=analyst_id,
        company_id=company_id,
        market_id=market_id,
        period=period
    )


@router.get("/{scorecard_id}", response_model=ScorecardDetailResponse)
async def get_scorecard(
    scorecard_id: UUID,
    db: Session = Depends(get_db)
):
    """스코어카드 상세 조회 (기간 > 애널리스트 > 리포트 > 평가 데이터 포함)"""
    service = ScorecardService(db)
    scorecard = service.get_scorecard(scorecard_id)
    if not scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # 관련 데이터 조회
    from app.models.analyst import Analyst
    from app.models.company import Company
    from app.models.evaluation import Evaluation
    from app.models.report import Report
    from app.models.evaluation_score import EvaluationScore
    
    # 애널리스트 정보
    analyst = db.query(Analyst).filter(Analyst.id == scorecard.analyst_id).first()
    
    # 기업 정보
    company = None
    if scorecard.company_id:
        company = db.query(Company).filter(Company.id == scorecard.company_id).first()
    
    # 평가 정보 (스코어카드의 evaluation_id 사용)
    evaluation = None
    evaluation_scores = []
    if scorecard.scorecard_data and "evaluation_id" in scorecard.scorecard_data:
        evaluation_id = scorecard.scorecard_data["evaluation_id"]
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if evaluation:
            evaluation_scores = db.query(EvaluationScore).filter(
                EvaluationScore.evaluation_id == evaluation.id
            ).all()
    
    # 리포트 정보
    reports = []
    if evaluation and evaluation.report_id:
        report = db.query(Report).filter(Report.id == evaluation.report_id).first()
        if report:
            reports.append(report)
    
    # 상세 응답 생성
    detail_response = ScorecardDetailResponse.model_validate(scorecard)
    
    # 추가 정보를 scorecard_data에 포함
    if not detail_response.scorecard_data:
        detail_response.scorecard_data = {}
    
    detail_response.scorecard_data["analyst"] = {
        "id": str(analyst.id) if analyst else None,
        "name": analyst.name if analyst else None,
        "firm": analyst.firm if analyst else None,
        "sector": analyst.sector if analyst else None,
    } if analyst else None
    
    detail_response.scorecard_data["company"] = {
        "id": str(company.id) if company else None,
        "name": company.name if company else None,
        "ticker": company.ticker if company else None,
        "sector": company.sector if company else None,
    } if company else None
    
    detail_response.scorecard_data["evaluation"] = {
        "id": str(evaluation.id) if evaluation else None,
        "status": evaluation.status if evaluation else None,
        "final_score": float(evaluation.final_score) if evaluation and evaluation.final_score else None,
        "evaluation_period": evaluation.evaluation_period if evaluation else None,
    } if evaluation else None
    
    detail_response.scorecard_data["reports"] = [
        {
            "id": str(r.id),
            "title": r.title,
            "publication_date": str(r.publication_date),
            "status": r.status,
        }
        for r in reports
    ]
    
    detail_response.scorecard_data["evaluation_scores"] = [
        {
            "score_type": es.score_type,
            "score_value": float(es.score_value),
            "weight": float(es.weight) if es.weight else None,
        }
        for es in evaluation_scores
    ]
    
    return detail_response


@router.get("/ranking", response_model=ScorecardRankingResponse)
async def get_scorecard_ranking(
    period: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """스코어카드 랭킹 조회"""
    service = ScorecardService(db)
    rankings = service.get_rankings(period=period, limit=limit)
    return ScorecardRankingResponse(
        rankings=[ScorecardResponse.model_validate(s) for s in rankings],
        period=period or service._get_current_period(),
        total=len(rankings)
    )

