"""
PDF 일괄 업로드 스크립트
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional
import aiofiles
import httpx

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.database import SessionLocal
from app.models.report import Report
from app.models.analyst import Analyst
from app.models.company import Company
from app.services.report_service import ReportService
from app.services.ai_agents.report_parsing_agent import ReportParsingAgent
from uuid import UUID
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_pdf_files(base_path: Path) -> List[Path]:
    """PDF 파일 찾기"""
    pdf_files = []
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(Path(root) / file)
    
    return pdf_files


def extract_company_name_from_filename(filename: str) -> Optional[str]:
    """파일명에서 기업명 추출"""
    # 파일명 패턴: 증권사_기업명_날짜.pdf
    parts = filename.replace('.pdf', '').split('_')
    
    # 기업명은 보통 두 번째 부분
    if len(parts) >= 2:
        company_name = parts[1]
        # 날짜 부분 제거
        company_name = company_name.split(' ')[0]
        return company_name
    
    return None


def extract_analyst_info_from_filename(filename: str) -> Optional[dict]:
    """파일명에서 애널리스트 정보 추출"""
    # 파일명 패턴: 증권사_기업명_날짜.pdf
    parts = filename.replace('.pdf', '').split('_')
    
    if len(parts) >= 1:
        firm_name = parts[0]
        return {
            "firm": firm_name,
            "name": None  # 파일명에서 이름 추출 불가
        }
    
    return None


async def upload_pdf_file(
    db: Session,
    file_path: Path,
    analyst_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None
) -> Optional[UUID]:
    """PDF 파일 업로드"""
    try:
        service = ReportService(db)
        
        # 파일 읽기
        async with aiofiles.open(file_path, 'rb') as f:
            file_content = await f.read()
        
        # UploadFile 객체 생성 (FastAPI 스타일)
        from fastapi import UploadFile
        from io import BytesIO
        
        file_obj = UploadFile(
            filename=file_path.name,
            file=BytesIO(file_content)
        )
        
        # 리포트 업로드
        result = await service.upload_and_extract(
            file=file_obj,
            analyst_id=analyst_id,
            company_id=company_id
        )
        
        logger.info(f"리포트 업로드 완료: {result.report_id} - {file_path.name}")
        return result.report_id
        
    except Exception as e:
        logger.error(f"리포트 업로드 실패 ({file_path.name}): {str(e)}")
        return None


async def find_or_create_analyst(
    db: Session,
    firm: str,
    name: Optional[str] = None
) -> Optional[UUID]:
    """애널리스트 찾기 또는 생성"""
    # 기존 애널리스트 검색
    analyst = db.query(Analyst).filter(
        Analyst.firm == firm
    ).first()
    
    if analyst:
        return analyst.id
    
    # 새 애널리스트 생성
    if name:
        analyst = Analyst(
            name=name,
            firm=firm,
            sector=None
        )
        db.add(analyst)
        db.commit()
        db.refresh(analyst)
        logger.info(f"새 애널리스트 생성: {name} ({firm})")
        return analyst.id
    
    return None


async def find_or_create_company(
    db: Session,
    company_name: str
) -> Optional[UUID]:
    """기업 찾기 또는 생성"""
    # 기존 기업 검색
    company = db.query(Company).filter(
        Company.name_kr == company_name
    ).first()
    
    if company:
        return company.id
    
    # 새 기업 생성
    company = Company(
        ticker=None,
        name_kr=company_name,
        name_en=None,
        sector=None
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    logger.info(f"새 기업 생성: {company_name}")
    return company.id


async def process_pdf_files(base_path: Path):
    """PDF 파일 일괄 처리"""
    pdf_files = find_pdf_files(base_path)
    logger.info(f"총 {len(pdf_files)}개의 PDF 파일 발견")
    
    db = SessionLocal()
    success_count = 0
    fail_count = 0
    
    try:
        for pdf_file in pdf_files:
            logger.info(f"처리 중: {pdf_file.name}")
            
            # 파일명에서 정보 추출
            analyst_info = extract_analyst_info_from_filename(pdf_file.name)
            company_name = extract_company_name_from_filename(pdf_file.name)
            
            analyst_id = None
            company_id = None
            
            # 애널리스트 찾기 또는 생성
            if analyst_info:
                analyst_id = await find_or_create_analyst(
                    db,
                    analyst_info["firm"],
                    analyst_info["name"]
                )
            
            # 기업 찾기 또는 생성
            if company_name:
                company_id = await find_or_create_company(db, company_name)
            
            # PDF 업로드
            report_id = await upload_pdf_file(
                db,
                pdf_file,
                analyst_id=analyst_id,
                company_id=company_id
            )
            
            if report_id:
                success_count += 1
            else:
                fail_count += 1
            
            # DB 세션 새로고침
            db.commit()
            
    finally:
        db.close()
    
    logger.info(f"처리 완료: 성공 {success_count}건, 실패 {fail_count}건")


if __name__ == "__main__":
    # PDF 폴더 경로
    pdf_folder = Path("/Users/seungminlee/Downloads/AAA 2/old_assets/Analyst PDF")
    
    if not pdf_folder.exists():
        logger.error(f"PDF 폴더를 찾을 수 없습니다: {pdf_folder}")
        sys.exit(1)
    
    asyncio.run(process_pdf_files(pdf_folder))

