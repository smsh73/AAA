"""
Companies router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.company import CompanyResponse
from app.services.company_service import CompanyService

router = APIRouter()


@router.get("", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    sector: Optional[str] = None,
    ticker: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """기업 목록 조회"""
    service = CompanyService(db)
    return service.get_companies(skip=skip, limit=limit, sector=sector, ticker=ticker)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """기업 상세 조회"""
    service = CompanyService(db)
    company = service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

