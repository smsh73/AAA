"""
Document extraction service
"""
from pathlib import Path
from typing import Dict, Any


class DocumentExtractionService:
    """문서 추출 서비스"""

    def __init__(self):
        pass

    async def extract_async(self, report_id: str, file_path: str) -> Dict[str, Any]:
        """비동기 문서 추출"""
        # 실제 구현: PDF 추출 로직
        # 1. Universal Document Scanner
        # 2. Universal Document Parser
        # 3. VLM 기반 이미지 분석
        # 4. AI 기반 보정 작업
        pass

