# AI가 찾은 스타 애널리스트 어워즈 시스템

멀티 LLM 기반 애널리스트 평가 및 어워드 선정 시스템

## 프로젝트 구조

```
analyst-awards-system/
├── apps/
│   ├── web/          # Next.js 프론트엔드
│   ├── api/          # FastAPI 백엔드
│   └── worker/       # Celery 워커
├── packages/
│   ├── shared/       # 공용 타입 및 스키마
│   ├── llm-adapters/ # LLM 어댑터 (OpenAI, Claude, Gemini, Perplexity)
│   └── document-extractor/ # PDF 문서 추출 시스템
└── infra/            # 인프라 설정 (Docker, K8s)
```

## 기술 스택

- **Frontend**: Next.js 14, TypeScript, TailwindCSS, React Query
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery
- **AI/ML**: OpenAI API, Anthropic API, Google Gemini API, Perplexity API
- **DevOps**: Docker, Kubernetes

## 시작하기

### 사전 요구사항

- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Python >= 3.10
- PostgreSQL >= 14
- Redis >= 7

### 설치

```bash
# 의존성 설치
pnpm install

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 API 키 등을 설정

# 데이터베이스 마이그레이션
cd apps/api
alembic upgrade head

# 개발 서버 시작
pnpm dev
```

## 개발 가이드

자세한 내용은 [통합_개발계획서.md](../통합_개발계획서.md)를 참조하세요.

