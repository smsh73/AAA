"""
Excel parser service
"""
import pandas as pd
from typing import List, Dict
from fastapi import UploadFile
import io


class ExcelParser:
    """Excel 파일 파서"""

    async def parse_excel(self, file: UploadFile) -> List[Dict]:
        """Excel 파일 파싱"""
        contents = await file.read()
        # 한글 인코딩을 명시적으로 처리
        excel_data = pd.read_excel(
            io.BytesIO(contents), 
            sheet_name=None, 
            engine='openpyxl',
            dtype=str  # 모든 데이터를 문자열로 읽어서 한글 처리 안정화
        )

        records = []
        
        for sheet_name, df in excel_data.items():
            # 컬럼명 정규화 (공백 제거)
            df.columns = df.columns.str.strip()
            
            # 가능한 컬럼명 매핑 (한글 컬럼명 우선)
            column_mapping = {
                'name': ['애널리스트 이름', '애널리스트명', '애널리스트', '이름', 'Name', 'name', 'NAME'],
                'firm': ['리서치센터', '증권사', '증권사명', '회사', 'Firm', 'firm', 'FIRM'],
                'department': ['세부 섹터', '부서', '소속부서', 'Department', 'department', 'DEPARTMENT'],
                'sector': ['담당 산업', '섹터', '업종', 'Sector', 'sector', 'SECTOR'],
                'email': ['이메일', 'Email', 'email', 'EMAIL', 'E-mail'],
            }
            
            # 컬럼명 찾기
            found_columns = {}
            for target_col, possible_names in column_mapping.items():
                for col in df.columns:
                    if col in possible_names:
                        found_columns[target_col] = col
                        break
            
            # 데이터 추출
            for idx, row in df.iterrows():
                try:
                    # 이름과 증권사는 필수
                    name = None
                    firm = None
                    
                    if 'name' in found_columns:
                        name_val = row.get(found_columns['name'])
                        if not pd.isna(name_val):
                            name = str(name_val).strip()
                    if 'firm' in found_columns:
                        firm_val = row.get(found_columns['firm'])
                        if not pd.isna(firm_val):
                            firm = str(firm_val).strip()
                    
                    # 이름이나 증권사가 없으면 스킵
                    if not name or not firm:
                        continue
                    
                    record = {
                        'name': name,
                        'firm': firm,
                    }
                    
                    # 부서
                    if 'department' in found_columns:
                        dept = row.get(found_columns['department'])
                        if not pd.isna(dept):
                            dept_str = str(dept).strip()
                            if dept_str:
                                record['department'] = dept_str
                    
                    # 섹터 (컬럼에서 먼저 확인, 없으면 시트명에서)
                    sector = None
                    if 'sector' in found_columns:
                        sector_val = row.get(found_columns['sector'])
                        if not pd.isna(sector_val):
                            sector_str = str(sector_val).strip()
                            if sector_str:
                                sector = sector_str
                    
                    # 시트명에서 섹터 추출 시도
                    if not sector:
                        sheet_lower = sheet_name.lower()
                        if '반도체' in sheet_name or 'semiconductor' in sheet_lower:
                            sector = '반도체'
                        elif '자동차' in sheet_name or 'auto' in sheet_lower or 'automotive' in sheet_lower:
                            sector = '자동차'
                        elif '방산' in sheet_name or 'defense' in sheet_lower:
                            sector = '방산'
                        elif '금융' in sheet_name or 'finance' in sheet_lower or 'financial' in sheet_lower:
                            sector = '금융'
                        else:
                            sector = sheet_name
                    
                    record['sector'] = sector
                    
                    # 이메일
                    if 'email' in found_columns:
                        email = row.get(found_columns['email'])
                        if not pd.isna(email):
                            email_str = str(email).strip()
                            if email_str:
                                record['email'] = email_str
                    
                    records.append(record)
                except Exception as e:
                    # 개별 행 처리 중 오류 발생 시 로그만 남기고 계속 진행
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"행 {idx + 1} 처리 중 오류: {str(e)}")
                    continue

        return records

