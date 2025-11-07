/**
 * Universal Document Parser
 * 텍스트, 표, 이미지 추출
 */
import pdfplumber from 'pdfplumber';
import { ExtractedText, ExtractedTable, ExtractedImage, LayoutInfo } from './extractor';

export interface ParsedDocument {
  texts: ExtractedText[];
  tables: ExtractedTable[];
  images: ExtractedImage[];
}

export class DocumentParser {
  async parse(filePath: string, layout: LayoutInfo): Promise<ParsedDocument> {
    const texts: ExtractedText[] = [];
    const tables: ExtractedTable[] = [];
    const images: ExtractedImage[] = [];

    const pdf = await pdfplumber.open(filePath);

    for (const pageLayout of layout.pages) {
      const page = pdf.pages[pageLayout.pageNumber - 1];

      // 텍스트 추출
      const pageText = page.extract_text();
      if (pageText) {
        texts.push({
          content: pageText,
          pageNumber: pageLayout.pageNumber,
          bbox: [0, 0, page.width, page.height],
          confidence: 'high',
          language: this.detectLanguage(pageText),
        });
      }

      // 표 추출
      const extractedTables = page.extract_tables();
      for (const table of extractedTables) {
        tables.push({
          pageNumber: pageLayout.pageNumber,
          data: table as string[][],
          bbox: [0, 0, page.width, page.height],
          confidence: 'medium',
        });
      }

      // 이미지 추출 (실제 구현 필요)
      // images.push(...);
    }

    await pdf.close();

    return { texts, tables, images };
  }

  private detectLanguage(text: string): string {
    // 간단한 언어 감지 (실제로는 더 정교한 로직 필요)
    const koreanRegex = /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/;
    return koreanRegex.test(text) ? 'ko' : 'en';
  }
}

