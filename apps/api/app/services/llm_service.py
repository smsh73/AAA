"""
LLM Service - 통합 LLM 서비스
"""
import os
from typing import Dict, Any, Optional
from openai import OpenAI
import anthropic
import google.generativeai as genai
import httpx


class LLMService:
    """통합 LLM 서비스"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")

    async def generate(
        self,
        llm_name: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """LLM 생성"""
        options = options or {}
        
        if llm_name == "openai":
            return await self._generate_openai(prompt, options)
        elif llm_name == "claude":
            return await self._generate_claude(prompt, options)
        elif llm_name == "gemini":
            return await self._generate_gemini(prompt, options)
        elif llm_name == "perplexity":
            return await self._generate_perplexity(prompt, options)
        else:
            raise ValueError(f"Unknown LLM: {llm_name}")

    async def _generate_openai(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 생성"""
        response = self.openai_client.chat.completions.create(
            model=options.get("model", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=options.get("max_tokens", 4000),
            temperature=options.get("temperature", 0.7),
        )
        
        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "model": response.model,
        }

    async def _generate_claude(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Claude 생성"""
        response = self.anthropic_client.messages.create(
            model=options.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=options.get("max_tokens", 4096),
            temperature=options.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}],
        )
        
        content = response.content[0]
        text = content.text if hasattr(content, 'text') else str(content)
        
        return {
            "content": text,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            "model": response.model,
        }

    async def _generate_gemini(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Gemini 생성"""
        generation_config = {
            "max_output_tokens": options.get("max_tokens", 4096),
            "temperature": options.get("temperature", 0.7),
        }
        
        response = self.gemini_model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return {
            "content": response.text,
            "model": "gemini-pro",
        }

    async def _generate_perplexity(self, prompt: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Perplexity 생성"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": options.get("model", "sonar"),
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": options.get("max_tokens", 100000),
                    "temperature": options.get("temperature", 0.2),
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
                "model": data.get("model", "sonar"),
            }

    async def embed(self, text: str, model: str = "openai") -> list:
        """텍스트 임베딩"""
        if model == "openai":
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text,
            )
            return response.data[0].embedding
        else:
            raise ValueError(f"Embedding not supported for {model}")

