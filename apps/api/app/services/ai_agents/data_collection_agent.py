"""
Data Collection Agent - 데이터 수집 에이전트
"""
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.data_collection_log import DataCollectionLog
from app.models.prompt_template import PromptTemplate
from app.services.perplexity_service import PerplexityService
from app.services.llm_service import LLMService


class DataCollectionAgent:
    """데이터 수집 에이전트"""

    def __init__(self, db: Session):
        self.db = db
        self.perplexity_service = PerplexityService()
        self.llm_service = LLMService()

    async def collect_data(
        self,
        analyst_id: UUID,
        collection_type: str,
        params: Dict[str, Any],
        collection_job_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """데이터 수집"""
        # 프롬프트 템플릿 조회
        template = self.db.query(PromptTemplate).filter(
            PromptTemplate.template_type == collection_type,
            PromptTemplate.is_active == True
        ).first()

        if not template:
            raise ValueError(f"Prompt template not found for {collection_type}")

        # 프롬프트 생성
        prompt = self._build_prompt(template.prompt_content, params)

        # Perplexity로 데이터 수집
        start_time = datetime.now()
        try:
            response = await self.perplexity_service.search(
                prompt,
                max_tokens=template.max_output_tokens
            )
            
            collection_time = (datetime.now() - start_time).total_seconds()
            
            # 수집된 데이터 파싱
            collected_data = self._parse_response(response, collection_type)

            # 로그 저장
            log = DataCollectionLog(
                analyst_id=analyst_id,
                company_id=UUID(params.get("company_id")) if params.get("company_id") else None,
                collection_job_id=collection_job_id,
                collection_type=collection_type,
                prompt_template_id=str(template.id),
                perplexity_request={"prompt": prompt, "params": params},
                perplexity_response=response,
                collected_data=collected_data,
                status="success",
                collection_time=collection_time,
                token_usage=response.get("usage", {}),
            )
            self.db.add(log)
            self.db.commit()

            return {
                "status": "success",
                "collected_data": collected_data,
                "collection_time": collection_time,
            }

        except Exception as e:
            collection_time = (datetime.now() - start_time).total_seconds()
            
            # 에러 로그 저장
            log = DataCollectionLog(
                analyst_id=analyst_id,
                company_id=UUID(params.get("company_id")) if params.get("company_id") else None,
                collection_job_id=collection_job_id,
                collection_type=collection_type,
                prompt_template_id=str(template.id),
                perplexity_request={"prompt": prompt, "params": params},
                status="failed",
                error_message=str(e),
                collection_time=collection_time,
            )
            self.db.add(log)
            self.db.commit()

            raise

    def _build_prompt(self, template: str, params: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        prompt = template
        for key, value in params.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        return prompt

    def _parse_response(self, response: Dict[str, Any], collection_type: str) -> Dict[str, Any]:
        """응답 파싱"""
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # JSON 파싱 시도
        import json
        try:
            # JSON 블록 추출
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
                return json.loads(json_str)
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except:
            pass

        # JSON 파싱 실패 시 원본 반환
        return {"raw_content": content}

