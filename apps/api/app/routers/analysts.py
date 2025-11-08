"""
Analysts router
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.analyst import Analyst
from app.schemas.analyst import AnalystCreate, AnalystUpdate, AnalystResponse, AnalystBulkImportResponse
from app.services.analyst_service import AnalystService
from app.services.excel_parser import ExcelParser

router = APIRouter()


@router.get("", response_model=List[AnalystResponse])
async def get_analysts(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = None,
    firm: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """애널리스트 목록 조회"""
    service = AnalystService(db)
    return service.get_analysts(skip=skip, limit=limit, sector=sector, firm=firm)


@router.get("/{analyst_id}", response_model=AnalystResponse)
async def get_analyst(analyst_id: UUID, db: Session = Depends(get_db)):
    """애널리스트 상세 조회"""
    service = AnalystService(db)
    analyst = service.get_analyst(analyst_id)
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")
    return analyst


@router.post("", response_model=AnalystResponse)
async def create_analyst(analyst: AnalystCreate, db: Session = Depends(get_db)):
    """애널리스트 생성"""
    service = AnalystService(db)
    return service.create_analyst(analyst)


@router.put("/{analyst_id}", response_model=AnalystResponse)
async def update_analyst(
    analyst_id: UUID,
    analyst: AnalystUpdate,
    db: Session = Depends(get_db)
):
    """애널리스트 수정"""
    service = AnalystService(db)
    updated_analyst = service.update_analyst(analyst_id, analyst)
    if not updated_analyst:
        raise HTTPException(status_code=404, detail="Analyst not found")
    return updated_analyst


@router.delete("/{analyst_id}")
async def delete_analyst(analyst_id: UUID, db: Session = Depends(get_db)):
    """애널리스트 삭제"""
    service = AnalystService(db)
    success = service.delete_analyst(analyst_id)
    if not success:
        raise HTTPException(status_code=404, detail="Analyst not found")
    return {"message": "Analyst deleted successfully"}


@router.post("/bulk-import", response_model=AnalystBulkImportResponse)
async def bulk_import_analysts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Excel 파일 기반 애널리스트 일괄 등록"""
    parser = ExcelParser()
    service = AnalystService(db)
    
    # Excel 파일 파싱
    records = await parser.parse_excel(file)
    
    # 일괄 등록 및 자료수집 시작
    result = await service.bulk_import_and_start_collection(records)
    
    return result

