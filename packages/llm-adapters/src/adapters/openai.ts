/**
 * OpenAI Adapter
 */
import OpenAI from 'openai';
import { LLMAdapter, LLMOptions, LLMResponse } from './base';

export class OpenAIAdapter implements LLMAdapter {
  private client: OpenAI;

  constructor(apiKey: string) {
    this.client = new OpenAI({ apiKey });
  }

  async generate(prompt: string, options?: LLMOptions): Promise<LLMResponse> {
    const response = await this.client.chat.completions.create({
      model: 'gpt-4',
      messages: [
        { role: 'user', content: prompt }
      ],
      max_tokens: options?.maxTokens || 4000,
      temperature: options?.temperature || 0.7,
      top_p: options?.topP || 1.0,
    });

    return {
      content: response.choices[0]?.message?.content || '',
      usage: {
        promptTokens: response.usage?.prompt_tokens || 0,
        completionTokens: response.usage?.completion_tokens || 0,
        totalTokens: response.usage?.total_tokens || 0,
      },
      model: response.model,
    };
  }

  async embed(text: string): Promise<number[]> {
    const response = await this.client.embeddings.create({
      model: 'text-embedding-3-large',
      input: text,
    });

    return response.data[0].embedding;
  }
}

