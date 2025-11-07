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
        df = pd.read_excel(io.BytesIO(contents), sheet_name=None)

        records = []
        for sheet_name, sheet_df in df.items():
            for _, row in sheet_df.iterrows():
                record = {
                    "name": row.get("애널리스트명") or row.get("name", ""),
                    "firm": row.get("증권사명") or row.get("firm", ""),
                    "department": row.get("부서") or row.get("department"),
                    "sector": sheet_name or row.get("섹터") or row.get("sector"),
                    "email": row.get("이메일") or row.get("email"),
                }
                # 빈 값 제거
                record = {k: v for k, v in record.items() if v}
                if record.get("name") and record.get("firm"):
                    records.append(record)

        return records

