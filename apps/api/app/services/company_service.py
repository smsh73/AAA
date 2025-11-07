"""
Company service
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.company import Company
from app.schemas.company import CompanyResponse
from fastapi import HTTPException


class CompanyService:
    """기업 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        sector: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> List[Company]:
        """기업 목록 조회"""
        query = self.db.query(Company)

        if sector:
            query = query.filter(Company.sector == sector)
        if ticker:
            query = query.filter(Company.ticker == ticker)

        return query.offset(skip).limit(limit).all()

    def get_company(self, company_id: UUID) -> Optional[Company]:
        """기업 조회"""
        return self.db.query(Company).filter(Company.id == company_id).first()

