"""
Evaluations router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.evaluation import EvaluationStartRequest, EvaluationResponse
from app.services.evaluation_service import EvaluationService

router = APIRouter()


@router.post("/start", response_model=EvaluationResponse)
async def start_evaluation(
    request: EvaluationStartRequest,
    db: Session = Depends(get_db)
):
    """평가 시작"""
    service = EvaluationService(db)
    return await service.start_evaluation(request.report_id)

