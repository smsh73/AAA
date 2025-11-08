"""
Data collection router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.schemas.data_collection import (
    DataCollectionStartRequest,
    DataCollectionStartResponse,
    DataCollectionStatusResponse,
    DataCollectionLogResponse
)
from app.models.data_collection_log import DataCollectionLog
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


@router.get("/logs", response_model=List[DataCollectionLogResponse])
async def get_collection_logs(
    analyst_id: Optional[UUID] = Query(None),
    collection_job_id: Optional[UUID] = Query(None),
    collection_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """데이터 수집 로그 조회"""
    query = db.query(DataCollectionLog)
    
    if analyst_id:
        query = query.filter(DataCollectionLog.analyst_id == analyst_id)
    if collection_job_id:
        query = query.filter(DataCollectionLog.collection_job_id == collection_job_id)
    if collection_type:
        query = query.filter(DataCollectionLog.collection_type == collection_type)
    
    logs = query.order_by(DataCollectionLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/analysts/{analyst_id}/logs", response_model=List[DataCollectionLogResponse])
async def get_analyst_collection_logs(
    analyst_id: UUID,
    collection_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """애널리스트별 데이터 수집 로그 조회"""
    query = db.query(DataCollectionLog).filter(DataCollectionLog.analyst_id == analyst_id)
    
    if collection_type:
        query = query.filter(DataCollectionLog.collection_type == collection_type)
    
    logs = query.order_by(DataCollectionLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

