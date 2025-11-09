"""
Report Parsing Agent - 리포트 파싱 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any
from pathlib import Path

from app.models.report import Report, ReportSection, ExtractedText, ExtractedTable, ExtractedImage
from app.models.enums import ReportStatus
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

        report.status = ReportStatus.COMPLETED.value
        self.db.commit()

        return {
            "report_id": report_id,
            "sections": sections,
            "extraction_result": extraction_result,
        }

    async def _extract_sections(self, extraction_result: Dict[str, Any]) -> list:
        """섹션 추출 - LLM을 활용한 실제 섹션 분석"""
        texts = extraction_result.get("texts", [])
        tables = extraction_result.get("tables", [])
        
        # 텍스트 결합 (처음 8000자, 너무 길면 LLM 토큰 제한)
        combined_text = "\n".join([t.get("content", "") for t in texts[:50]])  # 최대 50개 텍스트 블록
        if len(combined_text) > 8000:
            combined_text = combined_text[:8000] + "..."
        
        # 표 정보 추가
        table_summaries = []
        for table in tables[:5]:  # 최대 5개 표
            table_data = table.get("data", [])
            if table_data:
                # 표의 첫 행(헤더)과 몇 개 행만 요약
                table_summary = f"\n[표 {table.get('page_number', 0)}페이지]: "
                if len(table_data) > 0:
                    table_summary += " | ".join([str(cell) for cell in table_data[0][:5]])  # 헤더만
                table_summaries.append(table_summary)
        
        combined_text += "\n\n" + "\n".join(table_summaries)
        
        prompt = f"""다음 증권사 애널리스트 리포트를 분석하여 섹션별로 구조화하세요.

리포트 내용:
{combined_text}

다음 섹션 타입을 찾아서 JSON 형식으로 반환하세요:
- summary: 요약, 개요, Executive Summary
- analysis: 분석, 기업분석, 실적분석, 재무분석
- forecast: 예측, 전망, 실적전망, 목표주가
- recommendation: 추천, 투자의견, 투자포인트
- risk: 위험요소, 리스크, 주의사항
- target_price: 목표주가 (숫자 포함)
- investment_opinion: 투자의견 (매수/중립/매도 등)

각 섹션에 대해 다음 정보를 추출:
- section_type: 섹션 타입
- title: 섹션 제목
- content: 섹션 내용 (요약)
- page_number: 페이지 번호 (추정)

JSON 형식으로 반환:
{{
  "sections": [
    {{
      "section_type": "summary",
      "title": "요약",
      "content": "요약 내용...",
      "page_number": 1
    }},
    ...
  ]
}}

반드시 유효한 JSON만 반환하세요."""
        
        try:
            result = await self.llm_service.generate("openai", prompt, {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.3
            })
            
            content = result.get("content", "")
            
            # JSON 추출 (마크다운 코드 블록 제거)
            import json
            import re
            
            # JSON 코드 블록에서 JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                sections = parsed.get("sections", [])
                
                # 페이지 번호 보정 (텍스트 블록의 페이지 번호 참조)
                for section in sections:
                    if not section.get("page_number"):
                        # 텍스트 블록에서 해당 내용이 있는 페이지 찾기
                        section_title = section.get("title", "").lower()
                        section_content = section.get("content", "").lower()
                        
                        for text_block in texts:
                            text_content = text_block.get("content", "").lower()
                            if section_title in text_content or any(word in text_content for word in section_content.split()[:3]):
                                section["page_number"] = text_block.get("page_number", 1)
                                break
                        
                        if not section.get("page_number"):
                            section["page_number"] = 1
                
                return sections
            else:
                # JSON 파싱 실패 시 기본 섹션 반환
                return self._create_default_sections(texts)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"섹션 추출 실패, 기본 섹션 사용: {str(e)}")
            return self._create_default_sections(texts)
    
    def _create_default_sections(self, texts: list) -> list:
        """기본 섹션 생성 (LLM 실패 시)"""
        if not texts:
            return []
        
        # 텍스트를 페이지별로 그룹화
        pages = {}
        for text in texts:
            page_num = text.get("page_number", 1)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(text.get("content", ""))
        
        sections = []
        order = 0
        
        # 첫 페이지를 요약으로
        if 1 in pages:
            sections.append({
                "section_type": "summary",
                "title": "요약",
                "content": " ".join(pages[1])[:500],  # 처음 500자
                "page_number": 1,
                "order": order
            })
            order += 1
        
        # 나머지 페이지를 분석으로
        for page_num in sorted(pages.keys()):
            if page_num > 1:
                sections.append({
                    "section_type": "analysis",
                    "title": f"분석 (페이지 {page_num})",
                    "content": " ".join(pages[page_num])[:1000],  # 처음 1000자
                    "page_number": page_num,
                    "order": order
                })
                order += 1
        
        return sections

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

