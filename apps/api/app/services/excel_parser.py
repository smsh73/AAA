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
        excel_data = pd.read_excel(io.BytesIO(contents), sheet_name=None, engine='openpyxl')

        records = []
        
        for sheet_name, df in excel_data.items():
            # 컬럼명 정규화 (공백 제거)
            df.columns = df.columns.str.strip()
            
            # 가능한 컬럼명 매핑
            column_mapping = {
                'name': ['이름', '애널리스트명', '애널리스트', 'Name', 'name', 'NAME'],
                'firm': ['증권사', '증권사명', '회사', 'Firm', 'firm', 'FIRM'],
                'department': ['부서', '소속부서', 'Department', 'department', 'DEPARTMENT'],
                'sector': ['섹터', '업종', 'Sector', 'sector', 'SECTOR'],
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
            for _, row in df.iterrows():
                # 이름과 증권사는 필수
                name = None
                firm = None
                
                if 'name' in found_columns:
                    name = row.get(found_columns['name'])
                if 'firm' in found_columns:
                    firm = row.get(found_columns['firm'])
                
                # 이름이나 증권사가 없으면 스킵
                if pd.isna(name) or pd.isna(firm) or not str(name).strip() or not str(firm).strip():
                    continue
                
                record = {
                    'name': str(name).strip(),
                    'firm': str(firm).strip(),
                }
                
                # 부서
                if 'department' in found_columns:
                    dept = row.get(found_columns['department'])
                    if not pd.isna(dept) and str(dept).strip():
                        record['department'] = str(dept).strip()
                
                # 섹터 (시트명 또는 컬럼에서)
                sector = None
                if 'sector' in found_columns:
                    sector_val = row.get(found_columns['sector'])
                    if not pd.isna(sector_val) and str(sector_val).strip():
                        sector = str(sector_val).strip()
                
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
                    if not pd.isna(email) and str(email).strip():
                        record['email'] = str(email).strip()
                
                records.append(record)

        return records

