# PDF 문서 처리 파이프라인 기획안

## 1. 개요

### 1.1 목적
애널리스트 리포트 PDF 문서를 정확하게 추출하고 구조화된 데이터로 변환하기 위한 지능형 문서 처리 파이프라인 구축

### 1.2 핵심 목표
- PDF 문서의 전체 레이아웃 정확한 스캔
- 텍스트, 표, 이미지, 차트, 그래프 등 다양한 요소 추출
- AI 기반 추출 내용 보정 및 검증
- VLM을 활용한 이미지 내 복잡한 수치 데이터 추출

## 2. 시스템 아키텍처

### 2.1 전체 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF 문서 입력                              │
│              (애널리스트 리포트 PDF 파일)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│    Phase 1: Universal Document Scanner                      │
│    - PDF 레이아웃 분석                                        │
│    - 페이지 구조 파악                                        │
│    - 요소 영역 식별                                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│    Phase 2: Universal Document Parser                        │
│    - 텍스트 추출                                             │
│    - 표 추출 (표 안의 텍스트 포함)                            │
│    - 이미지 추출                                             │
│    - 이미지 내 텍스트 추출 (OCR)                              │
│    - 차트/그래프 식별 및 추출                                │
│    - 레이아웃 구조 파악                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│    Phase 3: AI 기반 보정 작업                                 │
│    - 추출된 텍스트 보정                                      │
│    - 표 데이터 검증 및 보정                                  │
│    - 구조화된 데이터 변환                                    │
│    - 맥락 기반 오류 수정                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│    Phase 4: VLM 기반 이미지 분석                              │
│    - 이미지 내 텍스트 추출                                    │
│    - 차트/그래프 데이터 추출                                 │
│    - 복잡한 수치 데이터 추출                                 │
│    - 표 이미지 데이터 추출                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│    Phase 5: 데이터 통합 및 검증                               │
│    - 추출 데이터 통합                                        │
│    - 일관성 검증                                             │
│    - 최종 구조화된 데이터 생성                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│               구조화된 데이터 출력                             │
│              (JSON / 데이터베이스 저장)                        │
└──────────────────────────────────────────────────────────────┘
```

## 3. Phase 1: Universal Document Scanner

### 3.1 목적
PDF 문서의 전체 레이아웃을 스캔하여 문서 구조를 파악하고, 다양한 요소의 영역을 식별

### 3.2 기능 요건

#### 3.2.1 레이아웃 분석
- **페이지 구조 파악**
  - 헤더/푸터 영역 식별
  - 본문 영역 식별
  - 여백 분석
  - 컬럼 구조 파악 (1단, 2단, 다단)

- **요소 영역 식별**
  - 텍스트 블록 영역
  - 표 영역
  - 이미지 영역
  - 차트/그래프 영역
  - 수식 영역

#### 3.2.2 기술 스택
- **PDF 파싱 라이브러리**
  - PyPDF2 / pdfplumber
  - pdfminer.six
  - Apache PDFBox (Java 기반)

- **레이아웃 분석**
  - LayoutLM (Microsoft)
  - Detectron2 (Facebook)
  - PaddleOCR (레이아웃 분석 모드)

#### 3.2.3 출력 형식
```json
{
  "document_metadata": {
    "total_pages": 50,
    "page_width": 595,
    "page_height": 842,
    "file_size": 1024000
  },
  "pages": [
    {
      "page_number": 1,
      "layout": {
        "header": {
          "bbox": [0, 0, 595, 50],
          "confidence": 0.95
        },
        "body": {
          "bbox": [50, 50, 545, 792],
          "columns": 1
        },
        "footer": {
          "bbox": [0, 792, 595, 842],
          "confidence": 0.90
        }
      },
      "elements": [
        {
          "type": "text_block",
          "bbox": [50, 100, 545, 200],
          "confidence": 0.98
        },
        {
          "type": "table",
          "bbox": [50, 250, 545, 450],
          "confidence": 0.95
        },
        {
          "type": "image",
          "bbox": [50, 500, 545, 700],
          "confidence": 0.92
        },
        {
          "type": "chart",
          "bbox": [50, 750, 545, 792],
          "confidence": 0.88
        }
      ]
    }
  ]
}
```

## 4. Phase 2: Universal Document Parser

### 4.1 목적
스캔된 레이아웃 정보를 기반으로 각 요소에서 실제 콘텐츠를 추출

### 4.2 기능 요건

#### 4.2.1 텍스트 추출
- **일반 텍스트 추출**
  - 본문 텍스트 추출
  - 제목/부제목 추출
  - 리스트 항목 추출
  - 문단 구조 유지

- **텍스트 메타데이터**
  - 폰트 크기, 스타일 정보
  - 텍스트 위치 정보
  - 텍스트 순서 정보

#### 4.2.2 표 추출
- **표 구조 파악**
  - 행/열 구조 식별
  - 헤더 행 식별
  - 병합된 셀 처리
  - 표 안의 텍스트 추출

- **표 데이터 구조화**
  - CSV 형식 변환
  - JSON 형식 변환
  - 테이블 구조 유지

#### 4.2.3 이미지 추출
- **이미지 추출**
  - 원본 해상도 유지
  - 이미지 포맷 (PNG, JPEG 등)
  - 이미지 메타데이터

#### 4.2.4 이미지 내 텍스트 추출 (OCR)
- **OCR 처리**
  - 이미지 내 텍스트 인식
  - 텍스트 위치 정보 (bounding box)
  - 신뢰도 점수

#### 4.2.5 차트/그래프 식별 및 추출
- **차트/그래프 식별**
  - 차트 타입 식별 (막대, 선, 원형 등)
  - 차트 영역 추출
  - 차트 메타데이터

#### 4.2.6 기술 스택
- **PDF 파싱**
  - pdfplumber (표 추출 특화)
  - camelot (표 추출)
  - tabula-py (표 추출)

- **OCR**
  - Tesseract OCR
  - PaddleOCR
  - EasyOCR

- **이미지 처리**
  - OpenCV
  - PIL/Pillow

#### 4.2.7 출력 형식
```json
{
  "page_number": 1,
  "text_blocks": [
    {
      "id": "text_1",
      "content": "본문 텍스트 내용...",
      "bbox": [50, 100, 545, 200],
      "font_size": 12,
      "font_style": "normal",
      "order": 1
    }
  ],
  "tables": [
    {
      "id": "table_1",
      "bbox": [50, 250, 545, 450],
      "rows": 10,
      "columns": 5,
      "data": [
        ["헤더1", "헤더2", "헤더3", "헤더4", "헤더5"],
        ["데이터1", "데이터2", "데이터3", "데이터4", "데이터5"],
        ...
      ],
      "structure": {
        "header_row": 0,
        "merged_cells": []
      }
    }
  ],
  "images": [
    {
      "id": "image_1",
      "bbox": [50, 500, 545, 700],
      "image_path": "/path/to/image_1.png",
      "width": 495,
      "height": 200,
      "format": "PNG"
    }
  ],
  "charts": [
    {
      "id": "chart_1",
      "bbox": [50, 750, 545, 792],
      "type": "bar_chart",
      "image_path": "/path/to/chart_1.png"
    }
  ]
}
```

## 5. Phase 3: AI 기반 보정 작업

### 5.1 목적
추출된 내용의 오류를 수정하고, 맥락을 고려하여 데이터를 구조화

### 5.2 기능 요건

#### 5.2.1 텍스트 보정
- **OCR 오류 수정**
  - 잘못 인식된 문자 수정
  - 맥락 기반 오류 수정
  - 숫자/날짜 형식 정규화

- **텍스트 정제**
  - 불필요한 공백 제거
  - 줄바꿈 정리
  - 특수문자 정규화

#### 5.2.2 표 데이터 검증 및 보정
- **표 구조 검증**
  - 행/열 일관성 확인
  - 병합 셀 처리 검증
  - 헤더 행 식별 검증

- **표 데이터 보정**
  - 숫자 형식 정규화
  - 날짜 형식 정규화
  - 단위 통일
  - 빈 셀 처리

#### 5.2.3 구조화된 데이터 변환
- **의미 기반 구조화**
  - 제목/부제목 계층 구조
  - 섹션 구분
  - 리스트 구조화

#### 5.2.4 기술 스택
- **AI 서비스 API**
  - OpenAI GPT-4 (텍스트 보정)
  - Claude 3.5 Sonnet (구조화)
  - Gemini Pro (표 데이터 검증)

#### 5.2.5 처리 예시

**입력 (OCR 오류 포함)**:
```
삼성전자 2024년 1분기 실적
매출액: 1,234,567억원 (전년 대비 10% 증가)
영업이익: 123,456억원 (전년 대비 15% 증가)
```

**출력 (보정 후)**:
```json
{
  "company": "삼성전자",
  "period": "2024Q1",
  "financials": {
    "revenue": {
      "value": 1234567,
      "unit": "억원",
      "yoy_change": 0.10,
      "yoy_change_percent": "10%"
    },
    "operating_profit": {
      "value": 123456,
      "unit": "억원",
      "yoy_change": 0.15,
      "yoy_change_percent": "15%"
    }
  }
}
```

## 6. Phase 4: VLM 기반 이미지 분석

### 6.1 목적
이미지, 차트, 그래프에서 복잡한 수치 데이터를 추출

### 6.2 기능 요건

#### 6.2.1 이미지 내 텍스트 추출
- **고급 OCR**
  - 복잡한 레이아웃의 텍스트 추출
  - 손글씨 인식
  - 다양한 폰트 인식

- **텍스트 위치 정보**
  - 텍스트 bounding box
  - 텍스트 순서
  - 텍스트 그룹핑

#### 6.2.2 차트/그래프 데이터 추출
- **차트 타입별 처리**
  - 막대 그래프: 데이터 값 추출
  - 선 그래프: 데이터 포인트 추출
  - 원형 그래프: 비율 및 값 추출
  - 표 형태 차트: 표 데이터 추출

- **차트 메타데이터**
  - X축/Y축 라벨
  - 범례 정보
  - 단위 정보
  - 기간 정보

#### 6.2.3 복잡한 수치 데이터 추출
- **표 이미지 데이터 추출**
  - 이미지로 저장된 표 추출
  - 행/열 구조 파악
  - 숫자 데이터 추출

- **수식 추출**
  - 수학 수식 인식
  - 수식 구조화

#### 6.2.4 기술 스택
- **VLM (Vision Language Model)**
  - GPT-4 Vision (OpenAI)
  - Claude 3.5 Sonnet with Vision (Anthropic)
  - Gemini Pro Vision (Google)

- **전문 이미지 분석**
  - Table Transformer (표 이미지)
  - ChartOCR (차트 데이터 추출)

#### 6.2.5 처리 예시

**입력**: 차트 이미지 (막대 그래프)

**출력**:
```json
{
  "chart_type": "bar_chart",
  "title": "2024년 1분기 실적",
  "x_axis": {
    "label": "항목",
    "values": ["매출액", "영업이익", "순이익"]
  },
  "y_axis": {
    "label": "금액",
    "unit": "억원",
    "min": 0,
    "max": 2000000
  },
  "data": [
    {
      "category": "매출액",
      "value": 1234567,
      "unit": "억원"
    },
    {
      "category": "영업이익",
      "value": 123456,
      "unit": "억원"
    },
    {
      "category": "순이익",
      "value": 98765,
      "unit": "억원"
    }
  ],
  "legend": null
}
```

## 7. Phase 5: 데이터 통합 및 검증

### 7.1 목적
모든 단계에서 추출된 데이터를 통합하고 일관성을 검증

### 7.2 기능 요건

#### 7.2.1 데이터 통합
- **추출 데이터 병합**
  - 텍스트 데이터 통합
  - 표 데이터 통합
  - 이미지 분석 결과 통합
  - 차트 데이터 통합

- **문서 구조 재구성**
  - 페이지 순서 유지
  - 섹션 구조 유지
  - 요소 간 관계 유지

#### 7.2.2 일관성 검증
- **데이터 일관성 확인**
  - 중복 데이터 확인
  - 충돌 데이터 해결
  - 숫자 형식 통일

- **완전성 검증**
  - 필수 데이터 존재 확인
  - 누락된 요소 확인
  - 데이터 품질 점수

#### 7.2.3 최종 구조화된 데이터 생성
- **통합 데이터 구조**
  - JSON 형식
  - 데이터베이스 저장 형식
  - 검색 가능한 형식

#### 7.2.4 출력 형식
```json
{
  "document_id": "doc_12345",
  "metadata": {
    "file_name": "analyst_report_2024.pdf",
    "total_pages": 50,
    "processed_at": "2024-01-16T10:00:00Z",
    "processing_time": 45.5,
    "quality_score": 0.92
  },
  "structure": {
    "title": "삼성전자 2024년 1분기 실적 분석",
    "sections": [
      {
        "section_id": "sec_1",
        "title": "실적 요약",
        "order": 1,
        "content": {
          "text_blocks": [...],
          "tables": [...],
          "images": [...],
          "charts": [...]
        }
      }
    ]
  },
  "extracted_data": {
    "financial_data": {
      "revenue": {
        "predicted": 1000000,
        "actual": 1234567,
        "unit": "억원"
      }
    },
    "predictions": [...],
    "tables": [...],
    "charts": [...]
  }
}
```

## 8. 기술 스택 요약

### 8.1 PDF 처리
- **라이브러리**
  - pdfplumber
  - PyPDF2
  - pdfminer.six
  - camelot (표 추출)
  - tabula-py (표 추출)

### 8.2 레이아웃 분석
- **도구**
  - LayoutLM
  - Detectron2
  - PaddleOCR (레이아웃 분석)

### 8.3 OCR
- **엔진**
  - Tesseract OCR
  - PaddleOCR
  - EasyOCR

### 8.4 이미지 처리
- **라이브러리**
  - OpenCV
  - PIL/Pillow
  - scikit-image

### 8.5 AI 서비스
- **API**
  - OpenAI GPT-4 / GPT-4 Vision
  - Claude 3.5 Sonnet / Claude 3.5 Sonnet with Vision
  - Gemini Pro / Gemini Pro Vision
  - Perplexity API (검증용)

### 8.6 VLM
- **모델**
  - GPT-4 Vision (OpenAI)
  - Claude 3.5 Sonnet with Vision (Anthropic)
  - Gemini Pro Vision (Google)

### 8.7 표 이미지 처리
- **전문 도구**
  - Table Transformer
  - ChartOCR
  - TableNet

## 9. 구현 알고리즘

### 9.1 전체 프로세스 알고리즘

```python
async def process_pdf_document(pdf_file_path):
    """
    PDF 문서 처리 전체 프로세스
    """
    # Phase 1: Universal Document Scanner
    layout_info = await scan_document_layout(pdf_file_path)
    
    # Phase 2: Universal Document Parser
    extracted_content = await parse_document_content(pdf_file_path, layout_info)
    
    # Phase 3: AI 기반 보정 작업
    corrected_content = await ai_correction(extracted_content)
    
    # Phase 4: VLM 기반 이미지 분석
    image_analysis_results = []
    for image in extracted_content['images']:
        vlm_result = await vlm_analyze_image(image)
        image_analysis_results.append(vlm_result)
    
    # Phase 5: 데이터 통합 및 검증
    final_data = await integrate_and_validate(
        corrected_content,
        image_analysis_results
    )
    
    return final_data
```

### 9.2 Universal Document Scanner 알고리즘

```python
async def scan_document_layout(pdf_file_path):
    """
    PDF 문서 레이아웃 스캔
    """
    import pdfplumber
    from layoutlm import LayoutLMProcessor
    
    layout_info = {
        "pages": []
    }
    
    with pdfplumber.open(pdf_file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # 페이지 메타데이터
            page_info = {
                "page_number": page_num,
                "width": page.width,
                "height": page.height,
                "layout": {},
                "elements": []
            }
            
            # 레이아웃 분석
            layout_processor = LayoutLMProcessor()
            layout_result = layout_processor.process_page(page)
            
            # 요소 영역 식별
            elements = identify_elements(layout_result)
            page_info["elements"] = elements
            
            layout_info["pages"].append(page_info)
    
    return layout_info
```

### 9.3 Universal Document Parser 알고리즘

```python
async def parse_document_content(pdf_file_path, layout_info):
    """
    문서 콘텐츠 추출
    """
    import pdfplumber
    import camelot
    from PIL import Image
    import pytesseract
    
    extracted_content = {
        "text_blocks": [],
        "tables": [],
        "images": [],
        "charts": []
    }
    
    with pdfplumber.open(pdf_file_path) as pdf:
        for page_info in layout_info["pages"]:
            page_num = page_info["page_number"]
            page = pdf.pages[page_num - 1]
            
            # 텍스트 추출
            text_blocks = extract_text_blocks(page, page_info["elements"])
            extracted_content["text_blocks"].extend(text_blocks)
            
            # 표 추출
            tables = camelot.read_pdf(pdf_file_path, pages=str(page_num))
            for table in tables:
                table_data = parse_table(table)
                extracted_content["tables"].append(table_data)
            
            # 이미지 추출
            images = extract_images(page, page_info["elements"])
            for image in images:
                # OCR 처리
                ocr_text = pytesseract.image_to_string(image["image"])
                image["ocr_text"] = ocr_text
                extracted_content["images"].append(image)
            
            # 차트/그래프 식별
            charts = identify_charts(page_info["elements"])
            extracted_content["charts"].extend(charts)
    
    return extracted_content
```

### 9.4 AI 기반 보정 알고리즘

```python
async def ai_correction(extracted_content):
    """
    AI 기반 추출 내용 보정
    """
    from openai import OpenAI
    from anthropic import Anthropic
    
    openai_client = OpenAI()
    claude_client = Anthropic()
    
    corrected_content = {
        "text_blocks": [],
        "tables": [],
        "images": []
    }
    
    # 텍스트 보정 (OpenAI GPT-4)
    for text_block in extracted_content["text_blocks"]:
        corrected_text = await correct_text_with_gpt4(
            openai_client,
            text_block["content"]
        )
        text_block["content"] = corrected_text
        text_block["correction_confidence"] = 0.95
        corrected_content["text_blocks"].append(text_block)
    
    # 표 데이터 보정 (Claude)
    for table in extracted_content["tables"]:
        corrected_table = await correct_table_with_claude(
            claude_client,
            table
        )
        corrected_content["tables"].append(corrected_table)
    
    # 구조화된 데이터 변환 (Gemini)
    structured_data = await structure_data_with_gemini(
        corrected_content
    )
    
    return structured_data
```

### 9.5 VLM 기반 이미지 분석 알고리즘

```python
async def vlm_analyze_image(image_info):
    """
    VLM을 활용한 이미지 분석
    """
    from openai import OpenAI
    from anthropic import Anthropic
    from google import generativeai as genai
    
    openai_client = OpenAI()
    claude_client = Anthropic()
    gemini_client = genai.GenerativeModel('gemini-pro-vision')
    
    image_path = image_info["image_path"]
    
    # 여러 VLM 모델로 분석 (Ensemble)
    results = []
    
    # GPT-4 Vision
    gpt4_result = await analyze_with_gpt4_vision(
        openai_client,
        image_path
    )
    results.append(gpt4_result)
    
    # Claude 3.5 Sonnet with Vision
    claude_result = await analyze_with_claude_vision(
        claude_client,
        image_path
    )
    results.append(claude_result)
    
    # Gemini Pro Vision
    gemini_result = await analyze_with_gemini_vision(
        gemini_client,
        image_path
    )
    results.append(gemini_result)
    
    # 결과 통합 (Consensus)
    final_result = integrate_vlm_results(results)
    
    return final_result
```

## 10. 성능 최적화

### 10.1 병렬 처리
- 각 페이지를 병렬로 처리
- 이미지 분석을 병렬로 처리
- AI API 호출을 배치로 처리

### 10.2 캐싱
- 동일 문서 재처리 방지
- 이미지 분석 결과 캐싱
- AI 보정 결과 캐싱

### 10.3 비용 최적화
- 불필요한 AI API 호출 최소화
- 배치 처리로 API 호출 효율화
- 캐싱으로 중복 호출 방지

## 11. 에러 처리

### 11.1 단계별 에러 처리
- 각 단계에서 발생할 수 있는 에러 처리
- 부분 실패 시에도 진행 가능한 구조
- 에러 로깅 및 알림

### 11.2 재시도 로직
- AI API 호출 실패 시 재시도
- 네트워크 오류 시 재시도
- 최대 재시도 횟수 제한

## 12. 품질 평가

### 12.1 추출 품질 지표
- 텍스트 추출 정확도
- 표 추출 정확도
- 이미지 분석 정확도
- 전체 품질 점수

### 12.2 검증 방법
- 수동 검증 샘플
- 자동 검증 로직
- 품질 점수 기반 필터링

