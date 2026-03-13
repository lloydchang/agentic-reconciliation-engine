import { createApiRef } from '@backstage/core-plugin-api';
import { DiscoveryApi, FetchApi } from '@backstage/core-plugin-api';

export interface RagAIRequest {
  message: string;
  category?: string;
  includeSources?: boolean;
  maxTokens?: number;
  temperature?: number;
}

export interface RagAIResponse {
  message: string;
  sources: string[];
  toolCalls: ToolCall[];
  confidence: number;
  processingTime: number;
}

export interface ToolCall {
  toolName: string;
  parameters: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  duration: number;
}

export interface RagAISearchRequest {
  query: string;
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}

export interface RagAISearchResponse {
  results: SearchResult[];
  total: number;
  facets: Record<string, any>;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  url?: string;
  score: number;
  metadata: Record<string, any>;
}

export const ragAiApiRef = createApiRef<RagAiApi>({
  id: 'rag-ai.api',
});

export interface RagAiApi {
  /**
   * Send a chat message to the RAG AI
   */
  chat(request: RagAIRequest): Promise<RagAIResponse>;

  /**
   * Search the RAG AI knowledge base
   */
  search(request: RagAISearchRequest): Promise<RagAISearchResponse>;

  /**
   * Get available tools
   */
  getTools(): Promise<any[]>;

  /**
   * Get available categories
   */
  getCategories(): Promise<string[]>;

  /**
   * Get tool details
   */
  getTool(toolName: string): Promise<any>;
}

/**
 * Client implementation for the RAG AI API
 */
export class RagAiApiClient implements RagAiApi {
  private readonly discoveryApi: DiscoveryApi;
  private readonly fetchApi: FetchApi;

  constructor(options: { discoveryApi: DiscoveryApi; fetchApi: FetchApi }) {
    this.discoveryApi = options.discoveryApi;
    this.fetchApi = options.fetchApi;
  }

  private async getBaseUrl(): Promise<string> {
    return await this.discoveryApi.getBaseUrl('rag-ai');
  }

  async chat(request: RagAIRequest): Promise<RagAIResponse> {
    const baseUrl = await this.getBaseUrl();
    const response = await this.fetchApi.fetch(`${baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async search(request: RagAISearchRequest): Promise<RagAISearchResponse> {
    const baseUrl = await this.getBaseUrl();
    const params = new URLSearchParams();

    params.append('query', request.query);
    if (request.limit) params.append('limit', request.limit.toString());
    if (request.offset) params.append('offset', request.offset.toString());
    if (request.filters) {
      params.append('filters', JSON.stringify(request.filters));
    }

    const response = await this.fetchApi.fetch(`${baseUrl}/search?${params}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getTools(): Promise<any[]> {
    const baseUrl = await this.getBaseUrl();
    const response = await this.fetchApi.fetch(`${baseUrl}/tools`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.tools;
  }

  async getCategories(): Promise<string[]> {
    const baseUrl = await this.getBaseUrl();
    const response = await this.fetchApi.fetch(`${baseUrl}/categories`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.categories;
  }

  async getTool(toolName: string): Promise<any> {
    const baseUrl = await this.getBaseUrl();
    const response = await this.fetchApi.fetch(`${baseUrl}/tools/${toolName}`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}
