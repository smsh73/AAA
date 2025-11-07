# 빠른 시작 가이드

## 시스템 요구사항

- Node.js >= 18.0.0
- pnpm >= 8.0.0
- Python >= 3.10
- PostgreSQL >= 14
- Redis >= 7
- Docker & Docker Compose (선택사항)

## 설치 및 실행

### 1. 환경 변수 설정

```bash
cd analyst-awards-system
cp .env.example .env
# .env 파일을 편집하여 API 키 등을 설정
```

### 2. Docker Compose로 실행 (권장)

```bash
docker-compose up -d
```

### 3. 수동 설치 및 실행

#### 백엔드

```bash
cd apps/api

# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 프론트엔드 (향후 구현)

```bash
cd apps/web
pnpm install
pnpm dev
```

## API 엔드포인트

### Health Check
```
GET http://localhost:8000/api/health
```

### 애널리스트 일괄 등록
```
POST http://localhost:8000/api/analysts/bulk-import
Content-Type: multipart/form-data
file: [Excel 파일]
```

### 리포트 업로드
```
POST http://localhost:8000/api/reports/upload
Content-Type: multipart/form-data
file: [PDF 파일]
analyst_id: [UUID]
company_id: [UUID]
```

## 다음 단계

1. 데이터베이스 마이그레이션 실행
2. API 키 설정
3. 테스트 데이터 입력
4. 시스템 테스트

자세한 내용은 [통합_개발계획서.md](../통합_개발계획서.md)를 참조하세요.

