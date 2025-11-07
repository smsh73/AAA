/**
 * LLM Router
 * 작업 유형별 최적 LLM 선택
 */
import { LLMAdapter, LLMOptions, LLMResponse } from './adapters/base';
import { OpenAIAdapter } from './adapters/openai';
import { ClaudeAdapter } from './adapters/claude';
import { GeminiAdapter } from './adapters/gemini';
import { PerplexityAdapter } from './adapters/perplexity';

export type TaskType = 
  | 'generate' 
  | 'summarize' 
  | 'long_context' 
  | 'multimodal' 
  | 'realtime_search'
  | 'reasoning'
  | 'verification';

export class LLMRouter {
  private adapters: Map<string, LLMAdapter>;

  constructor(apiKeys: {
    openai: string;
    anthropic: string;
    google: string;
    perplexity: string;
  }) {
    this.adapters = new Map([
      ['openai', new OpenAIAdapter(apiKeys.openai)],
      ['claude', new ClaudeAdapter(apiKeys.anthropic)],
      ['gemini', new GeminiAdapter(apiKeys.google)],
      ['perplexity', new PerplexityAdapter(apiKeys.perplexity)],
    ]);
  }

  async route(
    taskType: TaskType,
    prompt: string,
    options?: LLMOptions
  ): Promise<LLMResponse> {
    const adapter = this.selectAdapter(taskType);
    return adapter.generate(prompt, options);
  }

  private selectAdapter(taskType: TaskType): LLMAdapter {
    switch (taskType) {
      case 'generate':
      case 'summarize':
      case 'reasoning':
        return this.adapters.get('openai')!;
      case 'long_context':
      case 'verification':
        return this.adapters.get('claude')!;
      case 'multimodal':
        return this.adapters.get('gemini')!;
      case 'realtime_search':
        return this.adapters.get('perplexity')!;
      default:
        return this.adapters.get('openai')!;
    }
  }

  getAdapter(name: string): LLMAdapter | undefined {
    return this.adapters.get(name);
  }
}

