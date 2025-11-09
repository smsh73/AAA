# PDF 분석 및 평가 시스템 구축 완료 보고서

## 개요

`/old_assets/Analyst PDF/` 폴더의 PDF 문서들을 구조적으로 분석하고, 한글과 수치를 인식하여 추출한 후 DB에 저장하고, 실제 데이터와 비교하여 KPI 기반 평가를 수행하는 시스템을 구축했습니다.

## 완료된 작업

### 1. PDF 일괄 업로드 스크립트 작성

**파일:** `apps/api/scripts/batch_upload_pdfs.py`

**기능:**
- PDF 폴더 하위의 모든 PDF 파일 자동 스캔
- 파일명에서 증권사, 기업명 자동 추출
- 애널리스트 및 기업 자동 매칭 또는 생성
- 리포트 일괄 업로드 및 파싱 시작

**주요 기능:**
- `find_pdf_files()`: 재귀적으로 PDF 파일 찾기
- `extract_company_name_from_filename()`: 파일명에서 기업명 추출
- `extract_analyst_info_from_filename()`: 파일명에서 증권사 정보 추출
- `find_or_create_analyst()`: 애널리스트 찾기 또는 생성
- `find_or_create_company()`: 기업 찾기 또는 생성
- `upload_pdf_file()`: PDF 파일 업로드 및 파싱 시작

### 2. 한글 및 수치 인식 강화

**파일:** `apps/api/app/services/document_extraction_service.py`

**개선 사항:**
- 수치 데이터 추출 기능 추가 (`_extract_numeric_data()`)
- 한글 컨텍스트와 함께 수치 인식
- 목표주가, 실적 예측, 주가 관련 수치 자동 추출

**추출 패턴:**
1. **목표주가**: "목표주가 120,000원", "TP 120000원", "Target Price: 120000"
2. **실적 예측**: "매출액 1조 2,000억원", "영업이익 500억원"
3. **주가 정보**: "현재주가 50,000원", "52주 최고가 60,000원"

**데이터 구조:**
```json
{
  "type": "target_price|performance|stock_price",
  "value": 숫자값,
  "unit": "원|억원|조원",
  "context": "원본 텍스트",
  "position": 문자 위치
}
```

### 3. OpenDART API 서비스 구현

**파일:** `apps/api/app/services/dart_service.py`

**기능:**
- 기업 기본 정보 조회
- 재무제표 조회 (분기별)
- 실적 데이터 추출 (매출액, 영업이익, 당기순이익 등)
- 기업명으로 검색

**주요 메서드:**
- `get_company_info()`: 기업 기본 정보
- `get_financial_statements()`: 재무제표 조회
- `get_quarterly_performance()`: 분기별 실적 조회
- `search_company_by_name()`: 기업명 검색

**환경 변수:**
- `DART_API_KEY`: OpenDART API 키 (필수)

### 4. KRX API 서비스 구현

**파일:** `apps/api/app/services/krx_service.py`

**기능:**
- 일별 주가 데이터 조회
- 현재 주가 조회
- 기간별 주가 통계 (최고가, 최저가, 평균가, 수익률 등)

**주요 메서드:**
- `get_stock_price()`: 일별 주가 데이터
- `get_current_price()`: 현재 주가
- `get_price_range()`: 기간별 주가 통계

**데이터 구조:**
```json
{
  "date": "날짜",
  "close_price": 종가,
  "open_price": 시가,
  "high_price": 고가,
  "low_price": 저가,
  "volume": 거래량,
  "change_rate": 변동률
}
```

### 5. 평가 프로세스 개선

**파일:** `apps/api/app/services/ai_agents/evaluation_agent.py`

**개선 사항:**
- OpenDART, KRX API 통합
- 예측 타입별 실제 데이터 수집
- ActualResult 자동 생성 및 업데이트

**데이터 수집 로직:**
1. **목표주가**: KRX API로 실제 주가 데이터 수집
2. **실적 예측** (매출액, 영업이익, 순이익): OpenDART API로 재무제표 데이터 수집
3. **기타 예측**: Perplexity API로 인터넷 검색

**주요 메서드:**
- `_collect_actual_data()`: 통합 실제 데이터 수집
- `_collect_target_price_actual()`: 목표주가 실제 데이터 (KRX)
- `_collect_performance_actual()`: 실적 실제 데이터 (OpenDART)
- `_collect_other_actual()`: 기타 예측 데이터 (Perplexity)

### 6. KPI 계산 로직 개선

**기존 구현:**
- 정확도 계산 로직은 이미 구현되어 있음
- 실제 데이터와 예측 데이터 비교

**개선 사항:**
- OpenDART/KRX API로 수집한 실제 데이터 활용
- 데이터 소스 명시 (KRX, OpenDART, Perplexity)
- 메타데이터 저장으로 상세 분석 가능

## 사용 방법

### 1. 환경 변수 설정

```bash
# .env 파일에 추가
DART_API_KEY=your_dart_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
```

### 2. PDF 일괄 업로드 실행

```bash
cd apps/api
python scripts/batch_upload_pdfs.py
```

**실행 결과:**
- PDF 파일 자동 스캔
- 애널리스트 및 기업 자동 매칭/생성
- 리포트 업로드 및 파싱 시작
- 수치 데이터 자동 추출

### 3. 평가 실행

리포트가 업로드되고 파싱이 완료되면:

1. 리포트 상세 페이지에서 "평가 시작" 버튼 클릭
2. 또는 API로 직접 평가 시작:
   ```bash
   POST /api/evaluations/start
   {
     "report_id": "report-uuid"
   }
   ```

**평가 프로세스:**
1. 리포트에서 예측 정보 추출 (OpenAI)
2. 실제 데이터 수집:
   - 목표주가 → KRX API
   - 실적 예측 → OpenDART API
   - 기타 → Perplexity API
3. 근거 분석 (Claude)
4. 정확도 계산 (Gemini)
5. KPI 점수 계산
6. 최종 점수 계산 (가중치 적용)

## 데이터 흐름

```
PDF 파일
  ↓
일괄 업로드 스크립트
  ↓
리포트 업로드 및 파싱
  ↓
한글 및 수치 추출
  ↓
예측 정보 추출 (OpenAI)
  ↓
실제 데이터 수집
  ├─ 목표주가 → KRX API
  ├─ 실적 예측 → OpenDART API
  └─ 기타 → Perplexity API
  ↓
정확도 계산
  ↓
KPI 점수 계산
  ↓
최종 점수 계산
  ↓
스코어카드 생성
```

## 주요 개선 효과

### 1. 자동화
- PDF 파일 자동 스캔 및 업로드
- 애널리스트 및 기업 자동 매칭
- 실제 데이터 자동 수집

### 2. 정확성 향상
- 공식 API (OpenDART, KRX) 활용으로 데이터 신뢰성 향상
- 한글 및 수치 인식 강화
- 컨텍스트 기반 수치 추출

### 3. 평가 정확도 향상
- 실제 데이터와 예측 비교
- 다양한 데이터 소스 활용
- 메타데이터 저장으로 상세 분석 가능

## 향후 개선 사항

### 1. PDF 파싱 개선
- 표 데이터 구조화 개선
- 차트/그래프 인식 강화
- 레이아웃 분석 개선

### 2. 데이터 수집 개선
- 실적 데이터 수집 정확도 향상
- 분기별 데이터 자동 매칭
- 데이터 캐싱으로 API 호출 최적화

### 3. 평가 로직 개선
- 예측 기간별 정확도 계산
- 가중치 조정 로직
- 벤치마크 비교 기능

## 테스트 권장 사항

1. **PDF 업로드 테스트**
   - 다양한 형식의 PDF 파일 테스트
   - 파일명 패턴 테스트
   - 한글 파일명 처리 테스트

2. **수치 추출 테스트**
   - 목표주가 추출 정확도
   - 실적 예측 추출 정확도
   - 다양한 형식의 수치 표현 테스트

3. **API 연동 테스트**
   - OpenDART API 연결 테스트
   - KRX API 연결 테스트
   - API 오류 처리 테스트

4. **평가 프로세스 테스트**
   - 실제 데이터 수집 테스트
   - 정확도 계산 테스트
   - KPI 점수 계산 테스트

## 결론

PDF 문서 분석 및 평가 시스템을 구축하여, 리포트의 한글 및 수치를 자동으로 추출하고, OpenDART 및 KRX API를 활용하여 실제 데이터를 수집한 후, KPI 기반 평가를 수행할 수 있게 되었습니다. 이를 통해 애널리스트의 예측 정확도를 체계적으로 평가할 수 있습니다.

