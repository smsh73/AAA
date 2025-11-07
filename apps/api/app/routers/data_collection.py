"""
Data collection router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.schemas.data_collection import (
    DataCollectionStartRequest,
    DataCollectionStartResponse,
    DataCollectionStatusResponse
)
from app.services.data_collection_service import DataCollectionService

router = APIRouter()


@router.post("/start", response_model=DataCollectionStartResponse)
async def start_data_collection(
    request: DataCollectionStartRequest,
    db: Session = Depends(get_db)
):
    """데이터 수집 시작"""
    service = DataCollectionService(db)
    return await service.start_collection(
        analyst_id=request.analyst_id,
        collection_types=request.collection_types,
        start_date=request.start_date,
        end_date=request.end_date
    )


@router.get("/{collection_job_id}/status", response_model=DataCollectionStatusResponse)
async def get_collection_status(
    collection_job_id: UUID,
    db: Session = Depends(get_db)
):
    """데이터 수집 상태 조회"""
    service = DataCollectionService(db)
    status = service.get_collection_status(collection_job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Collection job not found")
    return status

