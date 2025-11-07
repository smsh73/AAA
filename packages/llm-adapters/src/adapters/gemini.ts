/**
 * Gemini Adapter
 */
import { GoogleGenerativeAI } from '@google/generative-ai';
import { LLMAdapter, LLMOptions, LLMResponse } from './base';

export class GeminiAdapter implements LLMAdapter {
  private client: GoogleGenerativeAI;
  private model: any;

  constructor(apiKey: string) {
    this.client = new GoogleGenerativeAI(apiKey);
    this.model = this.client.getGenerativeModel({ model: 'gemini-pro' });
  }

  async generate(prompt: string, options?: LLMOptions): Promise<LLMResponse> {
    const generationConfig = {
      maxOutputTokens: options?.maxTokens || 4096,
      temperature: options?.temperature || 0.7,
      topP: options?.topP || 1.0,
    };

    const result = await this.model.generateContent({
      contents: [{ role: 'user', parts: [{ text: prompt }] }],
      generationConfig,
    });

    const response = result.response;
    const text = response.text();

    return {
      content: text,
      model: 'gemini-pro',
    };
  }

  async embed(text: string): Promise<number[]> {
    const model = this.client.getGenerativeModel({ model: 'text-embedding-004' });
    const result = await model.embedContent(text);
    return result.embedding.values;
  }
}

