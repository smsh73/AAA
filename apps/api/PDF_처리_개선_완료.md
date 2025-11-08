# PDF 처리 기능 개선 완료

## 개선 내역

### 1. DocumentExtractionService 구현 완료 ✅

이전에는 `pass`만 있던 `extract_async()` 메서드를 완전히 구현했습니다.

#### 구현된 기능

1. **메타데이터 추출**
   - PyPDF2를 사용하여 PDF 메타데이터 추출
   - 페이지 수, 제목, 작성자, 생성일 등

2. **텍스트 추출**
   - pdfplumber를 사용하여 전체 텍스트 추출
   - 단어별 추출 (위치 정보 포함)
   - 문단별 그룹화
   - 폰트 크기, 스타일 정보 추출

3. **표 추출**
   - pdfplumber의 `extract_tables()` 사용
   - 표 영역(bounding box) 자동 감지
   - 표 데이터 정제 및 구조화

4. **이미지 추출 및 OCR**
   - pdfplumber로 이미지 영역 감지
   - pdf2image로 페이지를 이미지로 변환
   - PaddleOCR로 이미지 내 텍스트 추출 (한국어 지원)

### 2. Report 모델 개선 ✅

- `status` 필드 추가: `pending`, `processing`, `completed`, `failed` 상태 추적

### 3. 리포트 태스크 개선 ✅

- `parse_report_task`에 async 래퍼 추가
- 실제 PDF 파싱 로직 실행
- 에러 처리 강화

### 4. 의존성 추가 ✅

- `pdf2image==1.16.3` 추가 (PDF를 이미지로 변환)

## 사용 방법

### 1. 리포트 업로드

```python
# API를 통해 리포트 업로드
POST /api/reports/upload
Content-Type: multipart/form-data

{
  "file": <PDF 파일>,
  "analyst_id": "...",
  "company_id": "..."
}
```

### 2. 추출 결과 확인

```python
# 리포트 상세 조회
GET /api/reports/{report_id}

# 추출된 텍스트 조회
GET /api/reports/{report_id}/texts

# 추출된 표 조회
GET /api/reports/{report_id}/tables

# 추출된 이미지 조회
GET /api/reports/{report_id}/images
```

## 추출 결과 형식

### 텍스트 블록
```json
{
  "id": "text_1_para_0",
  "content": "본문 텍스트...",
  "page_number": 1,
  "bbox": [50, 100, 495, 200],
  "font_size": 12,
  "font_style": "normal",
  "order": 0,
  "confidence": "high"
}
```

### 표
```json
{
  "id": "table_1_0",
  "page_number": 1,
  "data": [
    ["헤더1", "헤더2", "헤더3"],
    ["데이터1", "데이터2", "데이터3"]
  ],
  "rows": 2,
  "columns": 3,
  "bbox": [50, 250, 495, 450],
  "confidence": "high"
}
```

### 이미지
```json
{
  "id": "image_1_0",
  "page_number": 1,
  "image_path": "/path/to/image.png",
  "image_type": "image",
  "bbox": [50, 500, 495, 700],
  "width": 445,
  "height": 200,
  "ocr_text": "이미지에서 추출된 텍스트",
  "confidence": "high"
}
```

## 주의사항

### 1. PaddleOCR 초기화

PaddleOCR은 처음 사용 시 모델을 다운로드하므로 시간이 걸릴 수 있습니다.

```python
# PaddleOCR이 없어도 텍스트와 표 추출은 가능
# OCR은 선택적 기능
```

### 2. pdf2image 의존성

`pdf2image`는 시스템에 `poppler`가 설치되어 있어야 합니다.

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Docker:**
```dockerfile
RUN apt-get update && apt-get install -y poppler-utils
```

### 3. 이미지 추출

- pdfplumber는 이미지 직접 추출이 제한적입니다
- pdf2image를 사용하여 페이지를 이미지로 변환합니다
- 이미지가 없는 경우에도 텍스트와 표는 정상 추출됩니다

## 성능 최적화

1. **대용량 PDF 처리**
   - 페이지별로 순차 처리
   - 메모리 효율적 처리

2. **OCR 처리**
   - PaddleOCR은 필요할 때만 사용
   - 이미지가 있는 경우에만 OCR 실행

3. **에러 처리**
   - 각 페이지별로 독립적으로 처리
   - 한 페이지 오류가 전체 처리에 영향 없음

## 다음 단계

1. ✅ PDF 텍스트 추출 완료
2. ✅ 표 추출 완료
3. ✅ 이미지 추출 및 OCR 완료
4. ⏳ 섹션 구조 분석 (ReportParsingAgent에서 LLM 사용)
5. ⏳ 예측 정보 추출 (목표주가, 실적 예측 등)

## 테스트 방법

```python
# Python으로 직접 테스트
from app.services.document_extraction_service import DocumentExtractionService

service = DocumentExtractionService()
result = await service.extract_async(
    report_id="test-123",
    file_path="/path/to/report.pdf"
)

print(f"추출된 텍스트 블록: {len(result['texts'])}")
print(f"추출된 표: {len(result['tables'])}")
print(f"추출된 이미지: {len(result['images'])}")
```

