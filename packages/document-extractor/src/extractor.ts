/**
 * Universal Document Extractor
 */
import { DocumentScanner } from './scanner';
import { DocumentParser } from './parser';
import { VLMImageAnalyzer } from './vlm';

export interface ExtractionResult {
  texts: ExtractedText[];
  tables: ExtractedTable[];
  images: ExtractedImage[];
  metadata: DocumentMetadata;
}

export interface ExtractedText {
  content: string;
  pageNumber: number;
  bbox: [number, number, number, number];
  confidence: string;
  language: string;
}

export interface ExtractedTable {
  pageNumber: number;
  data: string[][];
  bbox: [number, number, number, number];
  confidence: string;
}

export interface ExtractedImage {
  pageNumber: number;
  imagePath: string;
  imageType: string;
  bbox: [number, number, number, number];
  analysisResult?: any;
}

export interface DocumentMetadata {
  pageCount: number;
  title?: string;
  author?: string;
  creationDate?: Date;
}

export class DocumentExtractor {
  private scanner: DocumentScanner;
  private parser: DocumentParser;
  private vlmAnalyzer: VLMImageAnalyzer;

  constructor() {
    this.scanner = new DocumentScanner();
    this.parser = new DocumentParser();
    this.vlmAnalyzer = new VLMImageAnalyzer();
  }

  async extract(filePath: string): Promise<ExtractionResult> {
    // 1. 문서 스캔 (레이아웃 분석)
    const layout = await this.scanner.scan(filePath);

    // 2. 문서 파싱 (텍스트, 표, 이미지 추출)
    const parsed = await this.parser.parse(filePath, layout);

    // 3. VLM 이미지 분석
    const analyzedImages = await Promise.all(
      parsed.images.map(img => 
        this.vlmAnalyzer.analyze(img.imagePath, img.imageType)
          .then(result => ({ ...img, analysisResult: result }))
      )
    );

    return {
      texts: parsed.texts,
      tables: parsed.tables,
      images: analyzedImages,
      metadata: layout.metadata,
    };
  }
}

