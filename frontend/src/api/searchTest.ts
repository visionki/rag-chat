import client from './client'

export interface SearchTestRequest {
  query: string
  top_k?: number
  embedding_provider_id?: number
}

export interface SearchResult {
  document_id: string
  filename: string
  chunk_index: number
  content: string
  score: number
  metadata: Record<string, any>
}

export interface SearchTestResponse {
  query: string
  top_k: number
  embedding_provider: string
  results: SearchResult[]
  total_time_ms: number
}

export interface EmbeddingProvider {
  id: number
  name: string
  model: string
  is_default: boolean
}

export const testSearch = (data: SearchTestRequest) => 
  client.post<SearchTestResponse>('/search-test', data)

export const getEmbeddingProviders = () =>
  client.get<EmbeddingProvider[]>('/search-test/providers')

