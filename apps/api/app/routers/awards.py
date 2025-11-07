"""
Awards router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.award import AwardResponse
from app.services.award_service import AwardService

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
    return service.get_awards(year=year, quarter=quarter, category=category)

