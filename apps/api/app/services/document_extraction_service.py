"""
Document extraction service
"""
import pdfplumber
import PyPDF2
from pathlib import Path
from typing import Dict, Any, List
from io import BytesIO
import os
import json
from PIL import Image
import base64

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False


class DocumentExtractionService:
    """문서 추출 서비스"""

    def __init__(self):
        self.ocr = None
        if PADDLEOCR_AVAILABLE:
            try:
                # PaddleOCR 초기화 (한국어, 영어 지원)
                self.ocr = PaddleOCR(use_angle_cls=True, lang='korean')
            except Exception as e:
                print(f"PaddleOCR 초기화 실패: {e}")
                self.ocr = None

    async def extract_async(self, report_id: str, file_path: str) -> Dict[str, Any]:
        """비동기 문서 추출"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {file_path}")

        result = {
            "pages": [],
            "texts": [],
            "tables": [],
            "images": [],
            "metadata": {}
        }

        # 1. 메타데이터 추출
        result["metadata"] = await self._extract_metadata(file_path)

        # 2. pdfplumber로 텍스트 및 표 추출
        # pdfplumber는 기본적으로 UTF-8을 사용하지만 명시적으로 설정
        try:
            with pdfplumber.open(file_path, encoding='utf-8') as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_result = await self._extract_page_content(
                        page, page_num, report_id, file_path
                    )
                    result["pages"].append(page_result)
                    result["texts"].extend(page_result.get("text_blocks", []))
                    result["tables"].extend(page_result.get("tables", []))
                    result["images"].extend(page_result.get("images", []))
        except TypeError:
            # pdfplumber.open()이 encoding 파라미터를 지원하지 않는 경우
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_result = await self._extract_page_content(
                        page, page_num, report_id, file_path
                    )
                    result["pages"].append(page_result)
                    result["texts"].extend(page_result.get("text_blocks", []))
                    result["tables"].extend(page_result.get("tables", []))
                    result["images"].extend(page_result.get("images", []))

        return result

    def _decode_pdf_string(self, value: Any) -> str:
        """PDF 문자열을 UTF-8로 디코딩"""
        if value is None:
            return ""
        
        if isinstance(value, bytes):
            try:
                # PDF 문자열은 여러 인코딩을 사용할 수 있음
                # 먼저 UTF-8 시도
                return value.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # CP949 (한국어 Windows 인코딩) 시도
                    return value.decode('cp949')
                except UnicodeDecodeError:
                    try:
                        # EUC-KR 시도
                        return value.decode('euc-kr')
                    except UnicodeDecodeError:
                        # 마지막으로 latin-1 시도 (손실 가능)
                        return value.decode('latin-1', errors='replace')
        
        if isinstance(value, str):
            return value
        
        return str(value)

    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """PDF 메타데이터 추출"""
        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                metadata = pdf.metadata or {}
                
                return {
                    "page_count": len(pdf.pages),
                    "title": self._decode_pdf_string(metadata.get("/Title", "")),
                    "author": self._decode_pdf_string(metadata.get("/Author", "")),
                    "subject": self._decode_pdf_string(metadata.get("/Subject", "")),
                    "creation_date": str(metadata.get("/CreationDate", "")),
                    "modification_date": str(metadata.get("/ModDate", "")),
                }
        except Exception as e:
            return {
                "page_count": 0,
                "error": str(e)
            }

    async def _extract_page_content(
        self,
        page: Any,
        page_num: int,
        report_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """페이지별 콘텐츠 추출"""
        result = {
            "page_number": page_num,
            "text_blocks": [],
            "tables": [],
            "images": []
        }

        # 1. 텍스트 추출
        text_blocks = await self._extract_text_blocks(page, page_num)
        result["text_blocks"] = text_blocks

        # 2. 표 추출
        tables = await self._extract_tables(page, page_num)
        result["tables"] = tables

        # 3. 이미지 추출 및 OCR
        images = await self._extract_images(page, page_num, report_id, file_path)
        result["images"] = images

        return result

    async def _extract_text_blocks(
        self,
        page: Any,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """텍스트 블록 추출"""
        text_blocks = []
        
        try:
            # 전체 텍스트 추출 (한글 인코딩 보장)
            full_text = page.extract_text()
            if full_text:
                # 텍스트 정제 (한글 깨짐 방지)
                if isinstance(full_text, bytes):
                    full_text = self._decode_pdf_string(full_text)
                elif not isinstance(full_text, str):
                    full_text = str(full_text)
                
                # 불필요한 공백 정리하되 한글은 유지
                full_text = full_text.strip()
                
                text_blocks.append({
                    "id": f"text_{page_num}_full",
                    "content": full_text,
                    "page_number": page_num,
                    "bbox": [0, 0, page.width, page.height],
                    "font_size": None,
                    "font_style": None,
                    "order": 0,
                    "confidence": "high",
                    "language": "ko"  # 한글 기본값
                })

            # 단어별 추출 (위치 정보 포함) - 한글 및 수치 인식 강화
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=True,
                horizontal_ltr=True,
                vertical_ttb=True,
                extra_attrs=["fontname", "size"]
            )
            
            # 수치 데이터 추출 (한글과 함께)
            numeric_patterns = self._extract_numeric_data(full_text)
            if numeric_patterns:
                text_blocks.append({
                    "id": f"numeric_{page_num}",
                    "content": json.dumps(numeric_patterns, ensure_ascii=False),
                    "page_number": page_num,
                    "bbox": [0, 0, page.width, page.height],
                    "font_size": None,
                    "font_style": None,
                    "order": -1,  # 수치 데이터는 먼저 표시
                    "confidence": "high",
                    "language": "ko",
                    "data_type": "numeric"
                })

            if words:
                # 단어들을 문단으로 그룹화
                current_paragraph = []
                current_y = None
                paragraph_id = 0

                for word in words:
                    word_y = word.get("top", 0)
                    word_text = word.get("text", "")
                    
                    # 텍스트 인코딩 보정
                    if isinstance(word_text, bytes):
                        word_text = self._decode_pdf_string(word_text)
                    word["text"] = word_text
                    
                    # 새로운 문단 시작 (y 좌표 차이가 크면)
                    if current_y is None or abs(word_y - current_y) > 10:
                        if current_paragraph:
                            # 이전 문단 저장
                            paragraph_text = " ".join([w.get("text", "") for w in current_paragraph])
                            paragraph_text = paragraph_text.strip()
                            if paragraph_text:
                                text_blocks.append({
                                    "id": f"text_{page_num}_para_{paragraph_id}",
                                    "content": paragraph_text,
                                    "page_number": page_num,
                                    "bbox": self._calculate_bbox(current_paragraph),
                                    "font_size": current_paragraph[0].get("size") if current_paragraph else None,
                                    "font_style": "bold" if any(w.get("fontname", "").lower().find("bold") >= 0 for w in current_paragraph) else "normal",
                                    "order": paragraph_id,
                                    "confidence": "high",
                                    "language": "ko"
                                })
                                paragraph_id += 1
                        
                        current_paragraph = [word]
                        current_y = word_y
                    else:
                        current_paragraph.append(word)
                        current_y = word_y

                # 마지막 문단 저장
                if current_paragraph:
                    paragraph_text = " ".join([w.get("text", "") for w in current_paragraph])
                    paragraph_text = paragraph_text.strip()
                    if paragraph_text:
                        text_blocks.append({
                            "id": f"text_{page_num}_para_{paragraph_id}",
                            "content": paragraph_text,
                            "page_number": page_num,
                            "bbox": self._calculate_bbox(current_paragraph),
                            "font_size": current_paragraph[0].get("size") if current_paragraph else None,
                            "font_style": "bold" if any(w.get("fontname", "").lower().find("bold") >= 0 for w in current_paragraph) else "normal",
                            "order": paragraph_id,
                            "confidence": "high",
                            "language": "ko"
                        })

        except Exception as e:
            print(f"텍스트 추출 오류 (페이지 {page_num}): {e}")
            # 오류 발생 시 빈 텍스트라도 추가
            text_blocks.append({
                "id": f"text_{page_num}_error",
                "content": "",
                "page_number": page_num,
                "bbox": [0, 0, page.width, page.height],
                "confidence": "low",
                "error": str(e)
            })

        return text_blocks

    async def _extract_tables(
        self,
        page: Any,
        page_num: int
    ) -> List[Dict[str, Any]]:
        """표 추출"""
        tables = []
        
        try:
            # pdfplumber로 표 추출
            extracted_tables = page.extract_tables()
            
            for table_idx, table in enumerate(extracted_tables):
                if not table or len(table) == 0:
                    continue

                # 표 영역 찾기
                table_settings = {
                    "vertical_strategy": "lines_strict",
                    "horizontal_strategy": "lines_strict",
                    "explicit_vertical_lines": [],
                    "explicit_horizontal_lines": [],
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "edge_tolerance": 3,
                    "min_words_vertical": 3,
                    "min_words_horizontal": 1,
                }
                
                table_bbox = None
                try:
                    table_objects = page.find_tables(table_settings)
                    if table_objects and table_idx < len(table_objects):
                        bbox = table_objects[table_idx].bbox
                        table_bbox = [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]]
                except:
                    pass

                # 표 데이터 정제 (한글 인코딩 보장)
                cleaned_table = []
                for row in table:
                    if row:
                        cleaned_row = []
                        for cell in row:
                            if cell:
                                # 셀 텍스트 인코딩 보정
                                cell_text = cell
                                if isinstance(cell_text, bytes):
                                    cell_text = self._decode_pdf_string(cell_text)
                                elif not isinstance(cell_text, str):
                                    cell_text = str(cell_text)
                                cleaned_row.append(cell_text.strip())
                            else:
                                cleaned_row.append("")
                        cleaned_table.append(cleaned_row)

                if cleaned_table:
                    tables.append({
                        "id": f"table_{page_num}_{table_idx}",
                        "page_number": page_num,
                        "data": cleaned_table,
                        "rows": len(cleaned_table),
                        "columns": len(cleaned_table[0]) if cleaned_table else 0,
                        "bbox": table_bbox or [0, 0, page.width, page.height],
                        "confidence": "high" if table_bbox else "medium"
                    })

        except Exception as e:
            print(f"표 추출 오류 (페이지 {page_num}): {e}")

        return tables

    async def _extract_images(
        self,
        page: Any,
        page_num: int,
        report_id: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """이미지 추출 및 OCR"""
        images = []
        
        try:
            # pdfplumber로 이미지 추출
            page_images = page.images
            
            for img_idx, img in enumerate(page_images):
                try:
                    # 이미지 영역 정보
                    bbox = [
                        img.get("x0", 0),
                        img.get("top", 0),
                        img.get("width", 0),
                        img.get("height", 0)
                    ]

                    # 이미지 저장 경로 생성
                    storage_dir = Path(file_path).parent / "images"
                    storage_dir.mkdir(exist_ok=True)
                    image_path = storage_dir / f"{report_id}_page{page_num}_img{img_idx}.png"

                    # 이미지 추출 및 저장
                    try:
                        # PyPDF2로 이미지 추출 시도
                        with open(file_path, 'rb') as f:
                            pdf_reader = PyPDF2.PdfReader(f)
                            if page_num <= len(pdf_reader.pages):
                                page_obj = pdf_reader.pages[page_num - 1]
                                if '/XObject' in page_obj.get('/Resources', {}):
                                    xObject = page_obj['/Resources']['/XObject'].get_object()
                                    for obj in xObject:
                                        if xObject[obj]['/Subtype'] == '/Image':
                                            # 이미지 추출 (간단한 방법)
                                            pass
                        
                        # pdf2image로 페이지를 이미지로 변환 (대안)
                        try:
                            from pdf2image import convert_from_path
                            if os.path.exists(file_path):
                                page_images_pil = convert_from_path(
                                    file_path,
                                    first_page=page_num,
                                    last_page=page_num,
                                    dpi=300
                                )
                                if page_images_pil:
                                    page_images_pil[0].save(str(image_path))
                        except ImportError:
                            # pdf2image가 없으면 이미지 영역만 저장
                            pass
                        except Exception as e:
                            print(f"이미지 저장 오류: {e}")
                    except Exception as e:
                        print(f"이미지 추출 오류: {e}")

                    # OCR 처리
                    ocr_text = ""
                    if self.ocr and os.path.exists(image_path):
                        try:
                            ocr_result = self.ocr.ocr(str(image_path), cls=True)
                            if ocr_result and ocr_result[0]:
                                ocr_text = "\n".join([
                                    line[1][0] for line in ocr_result[0]
                                ])
                        except Exception as e:
                            print(f"OCR 오류: {e}")

                    images.append({
                        "id": f"image_{page_num}_{img_idx}",
                        "page_number": page_num,
                        "image_path": str(image_path),
                        "image_type": "image",
                        "bbox": bbox,
                        "width": bbox[2],
                        "height": bbox[3],
                        "ocr_text": ocr_text,
                        "confidence": "high" if ocr_text else "medium"
                    })

                except Exception as e:
                    print(f"이미지 추출 오류 (페이지 {page_num}, 이미지 {img_idx}): {e}")

        except Exception as e:
            print(f"이미지 추출 오류 (페이지 {page_num}): {e}")

        return images

    def _calculate_bbox(self, words: List[Dict]) -> List[float]:
        """단어 리스트로부터 bounding box 계산"""
        if not words:
            return [0, 0, 0, 0]
        
        x0 = min(w.get("x0", 0) for w in words)
        top = min(w.get("top", 0) for w in words)
        x1 = max(w.get("x1", 0) for w in words)
        bottom = max(w.get("bottom", 0) for w in words)
        
        return [x0, top, x1 - x0, bottom - top]
    
    def _extract_numeric_data(self, text: str) -> List[Dict[str, Any]]:
        """텍스트에서 수치 데이터 추출 (한글 컨텍스트 포함)"""
        import re
        
        numeric_data = []
        
        # 패턴 1: 목표주가 (예: "목표주가 120,000원", "TP 120000원")
        target_price_patterns = [
            r'목표주가\s*[:：]?\s*([\d,]+)\s*원',
            r'TP\s*[:：]?\s*([\d,]+)\s*원',
            r'Target\s*Price\s*[:：]?\s*([\d,]+)',
        ]
        
        for pattern in target_price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                price_str = match.group(1).replace(",", "")
                try:
                    price = float(price_str)
                    numeric_data.append({
                        "type": "target_price",
                        "value": price,
                        "unit": "원",
                        "context": match.group(0),
                        "position": match.start()
                    })
                except ValueError:
                    pass
        
        # 패턴 2: 실적 예측 (예: "매출액 1조 2,000억원", "영업이익 500억원")
        performance_patterns = [
            r'(매출액|영업이익|당기순이익|순이익)\s*[:：]?\s*([\d,]+)\s*(억|조|원|천억)',
            r'(Revenue|Operating\s*Profit|Net\s*Profit)\s*[:：]?\s*([\d,]+)',
        ]
        
        for pattern in performance_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                metric = match.group(1)
                value_str = match.group(2).replace(",", "")
                unit = match.group(3) if len(match.groups()) > 2 else ""
                
                try:
                    value = float(value_str)
                    # 단위 변환 (조, 억, 천억)
                    if "조" in unit or "trillion" in unit.lower():
                        value = value * 10000  # 조 -> 억
                    elif "천억" in unit:
                        value = value * 1000  # 천억 -> 억
                    
                    numeric_data.append({
                        "type": "performance",
                        "metric": metric,
                        "value": value,
                        "unit": unit or "억원",
                        "context": match.group(0),
                        "position": match.start()
                    })
                except ValueError:
                    pass
        
        # 패턴 3: 주가 관련 (예: "현재주가 50,000원", "52주 최고가 60,000원")
        stock_price_patterns = [
            r'(현재주가|현재가|주가|52주\s*최고가|52주\s*최저가)\s*[:：]?\s*([\d,]+)\s*원',
            r'(Current\s*Price|Stock\s*Price|52W\s*High|52W\s*Low)\s*[:：]?\s*([\d,]+)',
        ]
        
        for pattern in stock_price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                price_type = match.group(1)
                price_str = match.group(2).replace(",", "")
                try:
                    price = float(price_str)
                    numeric_data.append({
                        "type": "stock_price",
                        "price_type": price_type,
                        "value": price,
                        "unit": "원",
                        "context": match.group(0),
                        "position": match.start()
                    })
                except ValueError:
                    pass
        
        return numeric_data

