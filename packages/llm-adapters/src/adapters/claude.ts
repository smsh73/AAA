/**
 * Claude Adapter
 */
import Anthropic from '@anthropic-ai/sdk';
import { LLMAdapter, LLMOptions, LLMResponse } from './base';

export class ClaudeAdapter implements LLMAdapter {
  private client: Anthropic;

  constructor(apiKey: string) {
    this.client = new Anthropic({ apiKey });
  }

  async generate(prompt: string, options?: LLMOptions): Promise<LLMResponse> {
    const response = await this.client.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: options?.maxTokens || 4096,
      temperature: options?.temperature || 0.7,
      top_p: options?.topP || 1.0,
      messages: [
        { role: 'user', content: prompt }
      ],
    });

    const content = response.content[0];
    const text = content.type === 'text' ? content.text : '';

    return {
      content: text,
      usage: {
        promptTokens: response.usage.input_tokens,
        completionTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens,
      },
      model: response.model,
    };
  }

  async embed(text: string): Promise<number[]> {
    // Claude doesn't have a direct embedding API
    // This would need to be implemented using a different approach
    throw new Error('Claude embedding not implemented');
  }
}

