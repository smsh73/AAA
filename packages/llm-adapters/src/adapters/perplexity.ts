/**
 * Perplexity Adapter
 */
import { LLMAdapter, LLMOptions, LLMResponse } from './base';

export class PerplexityAdapter implements LLMAdapter {
  private apiKey: string;
  private baseUrl: string = 'https://api.perplexity.ai';
  private maxInputTokens: number = 1000000;
  private maxOutputTokens: number = 100000;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generate(prompt: string, options?: LLMOptions): Promise<LLMResponse> {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'sonar',
        messages: [
          { role: 'user', content: prompt }
        ],
        max_tokens: options?.maxTokens || this.maxOutputTokens,
        temperature: options?.temperature || 0.2,
        top_p: options?.topP || 0.9,
      }),
    });

    if (!response.ok) {
      throw new Error(`Perplexity API error: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      content: data.choices[0]?.message?.content || '',
      usage: data.usage,
      model: data.model,
    };
  }

  async embed(text: string): Promise<number[]> {
    throw new Error('Perplexity embedding not supported');
  }
}

