/**
 * Base LLM Adapter Interface
 */
export interface LLMAdapter {
  generate(prompt: string, options?: LLMOptions): Promise<LLMResponse>;
  embed(text: string): Promise<number[]>;
  tools?(tools: Tool[]): Promise<LLMResponse>;
}

export interface LLMOptions {
  maxTokens?: number;
  temperature?: number;
  topP?: number;
  stream?: boolean;
}

export interface LLMResponse {
  content: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model?: string;
}

export interface Tool {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

