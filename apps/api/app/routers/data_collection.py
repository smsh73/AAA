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
    """데이터 수집 시작 (통합 수집 포함)"""
    from app.tasks.data_collection_tasks import start_comprehensive_collection_task
    
    service = DataCollectionService(db)
    
    # CollectionJob 생성
    from app.models.collection_job import CollectionJob
    from app.models.analyst import Analyst
    from datetime import datetime, timedelta
    
    analyst = db.query(Analyst).filter(Analyst.id == request.analyst_id).first()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")
    
    job = CollectionJob(
        analyst_id=request.analyst_id,
        collection_types=request.collection_types,
        start_date=datetime.combine(request.start_date, datetime.min.time()),
        end_date=datetime.combine(request.end_date, datetime.max.time()),
        status="pending",
        progress={ct: {"total": 0, "completed": 0, "failed": 0} for ct in request.collection_types},
        overall_progress="0.0"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # 예상 완료 시간 계산
    estimated_minutes = len(request.collection_types) * 10  # 통합 수집은 더 오래 걸림
    estimated_completion = datetime.now() + timedelta(minutes=estimated_minutes)
    job.estimated_completion_time = estimated_completion
    db.commit()
    
    # 통합 수집 태스크 시작
    start_comprehensive_collection_task.delay(str(job.id))
    
    return DataCollectionStartResponse(
        collection_job_id=job.id,
        status=job.status,
        estimated_completion_time=job.estimated_completion_time
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


@router.get("/logs/realtime", response_model=List[DataCollectionLogResponse])
async def get_realtime_logs(
    collection_job_id: UUID = Query(...),
    last_log_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """실시간 로그 조회 (폴링용)"""
    query = db.query(DataCollectionLog).filter(
        DataCollectionLog.collection_job_id == collection_job_id
    )
    
    if last_log_id:
        query = query.filter(DataCollectionLog.id > last_log_id)
    
    logs = query.order_by(DataCollectionLog.created_at.asc()).limit(100).all()
    return logs

