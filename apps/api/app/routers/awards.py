"""
Awards router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.award import AwardResponse
from app.services.award_service import AwardService
from app.tasks.award_tasks import select_awards_task

router = APIRouter()


@router.get("", response_model=List[AwardResponse])
async def get_awards(
    year: int,
    quarter: Optional[int] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """어워드 조회"""
    service = AwardService(db)
    awards = service.get_awards(year=year, quarter=quarter, category=category)
    return awards


@router.post("/run")
async def run_award_selection(
    year: int,
    quarter: Optional[int] = None,
    categories: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """어워드 선정 실행"""
    service = AwardService(db)
    
    # 비동기 작업 시작
    task = select_awards_task.delay(year, quarter, categories)
    
    return {
        "task_id": task.id,
        "status": "started",
        "year": year,
        "quarter": quarter,
    }

