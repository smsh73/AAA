# 시스템 아키텍처

## 전체 구조

```
┌─────────────────────────────────────────┐
│         Frontend (Next.js/React)         │
│         - TypeScript                     │
│         - TailwindCSS                    │
│         - React Query                    │
└─────────────────┬─────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼─────────────────────────┐
│      Backend (FastAPI/Python)              │
│      ┌─────────────────────────────────┐  │
│      │  API Layer (FastAPI)            │  │
│      │  - Routers                      │  │
│      │  - Schemas (Pydantic)           │  │
│      └───────────┬─────────────────────┘  │
│                  │                         │
│      ┌───────────▼─────────────────────┐  │
│      │  Service Layer                  │  │
│      │  - Business Logic                │  │
│      │  - AI Agents (11개)             │  │
│      │  - LLM Service                  │  │
│      │  - Document Extraction          │  │
│      └───────────┬─────────────────────┘  │
│                  │                         │
│      ┌───────────▼─────────────────────┐  │
│      │  Data Layer                      │  │
│      │  - SQLAlchemy Models             │  │
│      │  - Database Session              │  │
│      └─────────────────────────────────┘  │
└─────────────────┬─────────────────────────┘
                  │
┌─────────────────▼─────────────────────────┐
│      Infrastructure                       │
│      - PostgreSQL (데이터베이스)          │
│      - Redis (캐시/메시지 브로커)         │
│      - Celery Workers (비동기 작업)       │
└───────────────────────────────────────────┘
```

## 기술 스택

### Frontend
- **Next.js 14**: React 프레임워크, 서버 컴포넌트 지원
- **TypeScript**: 타입 안정성
- **TailwindCSS**: 유틸리티 기반 CSS
- **React Query**: 서버 상태 관리

### Backend
- **FastAPI**: 고성능 Python 웹 프레임워크
- **Python 3.11+**: 메인 백엔드 언어
- **SQLAlchemy/SQLModel**: ORM 및 데이터베이스 추상화
- **Pydantic**: 데이터 검증 및 직렬화

### AI & ML
- **OpenAI SDK**: GPT-4 통합
- **Anthropic SDK**: Claude 3.5 Sonnet 통합
- **Google Generative AI**: Gemini Pro 통합
- **Perplexity API**: 실시간 검색 및 데이터 수집

### 문서 처리
- **pdfplumber**: PDF 텍스트 추출
- **PyPDF2**: PDF 메타데이터 처리
- **PaddleOCR**: OCR 처리
- **Pillow**: 이미지 처리

### 비동기 작업
- **Celery**: 분산 작업 큐
- **Redis**: 메시지 브로커 및 결과 백엔드

### 데이터베이스
- **PostgreSQL**: 메인 데이터베이스
- **Alembic**: 데이터베이스 마이그레이션

## 아키텍처 원칙

### 1. 단일 언어 백엔드 (Python)
- 모든 비즈니스 로직을 Python으로 구현
- AI/ML 라이브러리 풍부한 Python 생태계 활용
- 직접 함수 호출로 낮은 레이턴시

### 2. 명확한 계층 분리
- **API Layer**: HTTP 요청/응답 처리
- **Service Layer**: 비즈니스 로직
- **Data Layer**: 데이터베이스 접근

### 3. 비동기 처리
- Celery를 통한 장시간 작업 처리
- 리포트 파싱, 평가, 데이터 수집 등

### 4. 확장 가능한 구조
- 마이크로서비스로 분리 가능
- 수평 확장 용이
- 독립적인 배포 가능

## 데이터 흐름

### 리포트 업로드 및 평가 프로세스

```
1. 사용자 → Frontend: 리포트 업로드
2. Frontend → Backend API: POST /api/reports/upload
3. Backend API → Celery: 리포트 파싱 작업 큐에 추가
4. Celery Worker → DocumentExtractionService: PDF 파싱
5. Celery Worker → ReportParsingAgent: 섹션 추출
6. Celery Worker → EvaluationAgent: 평가 시작
7. EvaluationAgent → DataCollectionAgent: 데이터 수집
8. EvaluationAgent → LLM Service: AI 분석
9. EvaluationAgent → ScorecardService: 스코어카드 생성
10. Backend → Frontend: 평가 결과 반환
```

## AI 에이전트 구조

### 11개 AI 에이전트

1. **EvaluationAgent**: 평가 실행
2. **AwardAgent**: 어워드 선정
3. **ReportGenerationAgent**: 상세 보고서 생성
4. **ReportParsingAgent**: 리포트 파싱
5. **CompanyVerificationAgent**: 기업정보 검증
6. **PerformanceVerificationAgent**: 실적 검증
7. **StockTrackingAgent**: 추천종목 추적
8. **DataCollectionAgent**: 데이터 수집
9. **OrchestratorAgent**: 멀티 LLM 오케스트레이션
10. **PortfolioAnalysisAgent**: 포트폴리오 분석
11. **AnalystReportAgent**: 리포트 AI 분석

### LLM 역할 분담

- **OpenAI GPT-4**: 리포트 파싱, 추론, 구조화
- **Claude 3.5 Sonnet**: 장문 분석, 근거 검증, 상세 분석 작성
- **Gemini Pro**: 수치 검증, 차트 분석, 멀티모달 처리
- **Perplexity**: 실시간 데이터 수집, 팩트 체킹

## 보안

- JWT 기반 인증 (필요시)
- CORS 설정
- 환경 변수로 API 키 관리
- 입력 데이터 검증 (Pydantic)

## 성능 최적화

- Redis 캐싱
- Celery를 통한 비동기 처리
- 데이터베이스 인덱싱
- 연결 풀링

