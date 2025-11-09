"""
Evaluations router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.evaluation import (
    EvaluationStartRequest,
    EvaluationResponse,
    EvaluationListResponse,
    EvaluationGroupedResponse,
    EvaluationDetailResponse,
    EvaluationScoreResponse
)
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.get("", response_model=EvaluationListResponse)
async def get_evaluations(
    skip: int = 0,
    limit: int = 100,
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """평가 목록 조회"""
    service = EvaluationService(db)
    evaluations = service.get_evaluations(
        skip=skip,
        limit=limit,
        analyst_id=analyst_id,
        company_id=company_id,
        status=status
    )
    total = service.get_evaluations_count(
        analyst_id=analyst_id,
        company_id=company_id,
        status=status
    )
    return EvaluationListResponse(
        evaluations=[{
            "id": str(e.id),
            "report_id": str(e.report_id),
            "analyst_id": str(e.analyst_id),
            "company_id": str(e.company_id) if e.company_id else None,
            "evaluation_period": e.evaluation_period,
            "final_score": float(e.final_score) if e.final_score else None,
            "status": e.status,
            "created_at": e.created_at.isoformat(),
        } for e in evaluations],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(
    evaluation_id: UUID,
    db: Session = Depends(get_db)
):
    """평가 상세 조회"""
    service = EvaluationService(db)
    evaluation = service.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return EvaluationDetailResponse.model_validate(evaluation)


@router.get("/{evaluation_id}/scores", response_model=List[EvaluationScoreResponse])
async def get_evaluation_scores(
    evaluation_id: UUID,
    db: Session = Depends(get_db)
):
    """평가 점수 조회"""
    from app.models.evaluation import EvaluationScore
    
    scores = db.query(EvaluationScore).filter(
        EvaluationScore.evaluation_id == evaluation_id
    ).all()
    
    return [EvaluationScoreResponse.model_validate(s) for s in scores]


@router.get("/grouped", response_model=EvaluationGroupedResponse)
async def get_evaluations_grouped(
    period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """기간별 그룹화된 평가 조회 (기간>애널리스트>리포트)"""
    service = EvaluationService(db)
    result = service.get_evaluations_grouped_by_period(period=period)
    return EvaluationGroupedResponse(**result)


@router.post("/start", response_model=EvaluationResponse)
async def start_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db)
):
    """평가 시작"""
    service = EvaluationService(db)
    return await service.start_evaluation(request.report_id)

