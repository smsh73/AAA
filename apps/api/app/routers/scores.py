"""
Scores router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.services.scorecard_service import ScorecardService
from app.tasks.evaluation_tasks import run_evaluation_task

router = APIRouter()


class RecomputeScoreRequest(BaseModel):
    analyst_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    period: Optional[str] = None
    force: bool = False


@router.post("/recompute")
async def recompute_scores(
    request: RecomputeScoreRequest,
    db: Session = Depends(get_db)
):
    """스코어 재계산"""
    try:
        service = ScorecardService(db)
        
        if request.analyst_id:
            # 특정 애널리스트의 스코어 재계산
            result = await service.recompute_analyst_scores(
                analyst_id=request.analyst_id,
                period=request.period,
                force=request.force
            )
        elif request.company_id:
            # 특정 기업의 스코어 재계산
            result = await service.recompute_company_scores(
                company_id=request.company_id,
                period=request.period,
                force=request.force
            )
        else:
            # 전체 스코어 재계산
            result = await service.recompute_all_scores(
                period=request.period,
                force=request.force
            )
        
        return {
            "status": "completed",
            "message": "스코어 재계산이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스코어 재계산 실패: {str(e)}")


@router.get("")
async def get_scores(
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    period: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """스코어 조회"""
    try:
        service = ScorecardService(db)
        scores = service.get_scores(
            analyst_id=analyst_id,
            company_id=company_id,
            period=period,
            category=category,
            skip=skip,
            limit=limit
        )
        return scores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스코어 조회 실패: {str(e)}")

