# AI가 찾은 스타 애널리스트 어워즈 시스템

AI 기반 애널리스트 평가 및 어워즈 시스템

## 프로젝트 구조

```
analyst-awards-system/
├── apps/
│   ├── api/          # FastAPI 백엔드 (Python)
│   └── web/          # Next.js 프론트엔드 (React/TypeScript)
└── infra/            # 인프라 설정
```

## 기술 스택

### Backend (Python)
- FastAPI - 웹 프레임워크
- PostgreSQL - 데이터베이스
- Redis - 캐시 및 메시지 브로커
- Celery - 비동기 작업 큐
- SQLAlchemy/SQLModel - ORM
- OpenAI, Anthropic, Google AI SDK - LLM 통합
- pdfplumber, PyPDF2, PaddleOCR - PDF 처리

### Frontend
- Next.js 14
- React 18
- TypeScript
- TailwindCSS

### AI Services (Python SDK)
- OpenAI GPT-4 - 리포트 파싱, 추론, 구조화
- Claude 3.5 Sonnet - 장문 분석, 근거 검증
- Gemini Pro - 수치 검증, 차트 분석
- Perplexity - 실시간 데이터 수집

## 설치 및 실행

### 1. 환경 변수 설정

`.env` 파일 생성:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/analyst_awards

# Redis
REDIS_URL=redis://localhost:6379/0

# AI API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
PERPLEXITY_API_KEY=your_perplexity_key

# Storage
STORAGE_PATH=/app/storage
```

### 2. 데이터베이스 초기화

```bash
cd apps/api
python scripts/init_db.py
```

### 3. 백엔드 실행

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

### 4. Celery 워커 실행

```bash
cd apps/api
celery -A app.celery_app worker --loglevel=info
```

### 5. 프론트엔드 실행

```bash
cd apps/web
npm install
npm run dev
```

## API 엔드포인트

### 애널리스트
- `GET /api/analysts` - 애널리스트 목록 조회
- `POST /api/analysts/bulk-import` - 일괄 등록

### 리포트
- `POST /api/reports/upload` - 리포트 업로드
- `GET /api/reports/{report_id}/predictions` - 예측 정보 조회

### 평가
- `POST /api/evaluations/start` - 평가 시작
- `GET /api/evaluations/{evaluation_id}` - 평가 결과 조회

### 어워즈
- `GET /api/awards` - 어워즈 조회
- `POST /api/awards/run` - 어워즈 선정 실행

## 개발 가이드

자세한 개발 가이드는 `통합_개발계획서.md`를 참조하세요.
