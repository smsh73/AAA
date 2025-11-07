/**
 * Universal Document Scanner
 * PDF 레이아웃 분석
 */
import pdfplumber from 'pdfplumber';
import { DocumentMetadata } from './extractor';

export interface LayoutInfo {
  pages: PageLayout[];
  metadata: DocumentMetadata;
}

export interface PageLayout {
  pageNumber: number;
  elements: LayoutElement[];
}

export interface LayoutElement {
  type: 'text' | 'table' | 'image' | 'chart' | 'graph';
  bbox: [number, number, number, number];
  confidence: number;
}

export class DocumentScanner {
  async scan(filePath: string): Promise<LayoutInfo> {
    const pages: PageLayout[] = [];
    let metadata: DocumentMetadata = { pageCount: 0 };

    const pdf = await pdfplumber.open(filePath);
    metadata.pageCount = pdf.pages.length;

    for (let i = 0; i < pdf.pages.length; i++) {
      const page = pdf.pages[i];
      const elements: LayoutElement[] = [];

      // 텍스트 영역 식별
      const words = page.extract_words();
      if (words.length > 0) {
        elements.push({
          type: 'text',
          bbox: this.calculateBBox(words),
          confidence: 0.9,
        });
      }

      // 표 영역 식별
      const tables = page.extract_tables();
      for (const table of tables) {
        elements.push({
          type: 'table',
          bbox: [0, 0, page.width, page.height], // 실제로는 표 위치 계산 필요
          confidence: 0.8,
        });
      }

      pages.push({
        pageNumber: i + 1,
        elements,
      });
    }

    await pdf.close();

    return { pages, metadata };
  }

  private calculateBBox(words: any[]): [number, number, number, number] {
    if (words.length === 0) return [0, 0, 0, 0];

    const x0 = Math.min(...words.map(w => w.x0));
    const y0 = Math.min(...words.map(w => w.y0));
    const x1 = Math.max(...words.map(w => w.x1));
    const y1 = Math.max(...words.map(w => w.y1));

    return [x0, y0, x1 - x0, y1 - y0];
  }
}

