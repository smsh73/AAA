"""
Report Parsing Agent - 리포트 파싱 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any
from pathlib import Path

from app.models.report import Report, ReportSection, ExtractedText, ExtractedTable, ExtractedImage
from app.services.document_extraction_service import DocumentExtractionService
from app.services.llm_service import LLMService


class ReportParsingAgent:
    """리포트 파싱 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.extraction_service = DocumentExtractionService()
        self.llm_service = LLMService()

    async def parse_report(
        self,
        report_id: UUID,
        file_path: str
    ) -> Dict[str, Any]:
        """리포트 파싱"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 1. 문서 추출
        extraction_result = await self.extraction_service.extract_async(report_id, file_path)

        # 2. 섹션 추출 및 정규화
        sections = await self._extract_sections(extraction_result)

        # 3. 임베딩 생성
        embeddings = await self._generate_embeddings(extraction_result)

        # 4. 구조화된 데이터 저장
        await self._save_extracted_data(report_id, extraction_result, sections, embeddings)

        report.status = "completed"
        self.db.commit()

        return {
            "report_id": report_id,
            "sections": sections,
            "extraction_result": extraction_result,
        }

    async def _extract_sections(self, extraction_result: Dict[str, Any]) -> list:
        """섹션 추출"""
        # OpenAI로 섹션 구조 분석
        texts = extraction_result.get("texts", [])
        combined_text = "\n".join([t.get("content", "") for t in texts])
        
        prompt = f"""
다음 리포트 텍스트를 분석하여 섹션별로 구조화하세요:

{combined_text[:5000]}  # 처음 5000자만

섹션 타입:
- summary: 요약
- analysis: 분석
- forecast: 예측
- recommendation: 추천
- risk: 위험요소

각 섹션의 제목, 내용, 페이지 번호를 추출하세요.
"""
        result = await self.llm_service.generate("openai", prompt)
        
        # JSON 파싱 (실제 구현 필요)
        return [
            {
                "section_type": "summary",
                "title": "요약",
                "content": "",
                "page_number": 1,
            }
        ]

    async def _generate_embeddings(self, extraction_result: Dict[str, Any]) -> Dict[str, list]:
        """임베딩 생성"""
        embeddings = {}
        
        texts = extraction_result.get("texts", [])
        for text_data in texts:
            content = text_data.get("content", "")
            if content:
                embedding = await self.llm_service.embed(content)
                embeddings[text_data.get("id", "")] = embedding
        
        return embeddings

    async def _save_extracted_data(
        self,
        report_id: UUID,
        extraction_result: Dict[str, Any],
        sections: list,
        embeddings: Dict[str, list]
    ):
        """추출된 데이터 저장"""
        # 섹션 저장
        for section_data in sections:
            section = ReportSection(
                report_id=report_id,
                section_type=section_data.get("section_type"),
                title=section_data.get("title"),
                content=section_data.get("content"),
                page_number=section_data.get("page_number"),
                order=section_data.get("order", 0),
            )
            self.db.add(section)

        # 추출된 텍스트 저장
        for text_data in extraction_result.get("texts", []):
            text = ExtractedText(
                report_id=report_id,
                page_number=text_data.get("page_number", 1),
                content=text_data.get("content", ""),
                bbox=text_data.get("bbox"),
                confidence=text_data.get("confidence", "medium"),
                language=text_data.get("language", "ko"),
            )
            self.db.add(text)

        # 추출된 표 저장
        for table_data in extraction_result.get("tables", []):
            table = ExtractedTable(
                report_id=report_id,
                page_number=table_data.get("page_number", 1),
                table_data=table_data.get("data", []),
                bbox=table_data.get("bbox"),
                confidence=table_data.get("confidence", "medium"),
            )
            self.db.add(table)

        # 추출된 이미지 저장
        for image_data in extraction_result.get("images", []):
            image = ExtractedImage(
                report_id=report_id,
                page_number=image_data.get("page_number", 1),
                image_path=image_data.get("image_path", ""),
                image_type=image_data.get("image_type", "chart"),
                bbox=image_data.get("bbox"),
                analysis_result=image_data.get("analysis_result"),
            )
            self.db.add(image)

        self.db.flush()

