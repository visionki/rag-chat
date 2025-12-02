// LLM Provider
export interface LLMProvider {
  id: number
  name: string
  provider_type: string
  base_url: string | null
  models: string | null
  is_default: boolean
  is_active: boolean
  has_api_key: boolean
  created_at: string
  updated_at: string
}

export interface LLMProviderCreate {
  name: string
  provider_type: string
  base_url?: string
  api_key?: string
  models?: string
  is_default?: boolean
  is_active?: boolean
}

// Embedding Provider
export interface EmbeddingProvider {
  id: number
  name: string
  provider_type: string
  base_url: string | null
  model: string
  dimensions: number | null
  is_default: boolean
  is_active: boolean
  has_api_key: boolean
  created_at: string
  updated_at: string
}

export interface EmbeddingProviderCreate {
  name: string
  provider_type: string
  base_url?: string
  api_key?: string
  model: string
  dimensions?: number
  is_default?: boolean
  is_active?: boolean
}

// Document
export interface Document {
  id: number
  filename: string
  file_type: string
  file_size: number | null
  chunk_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  embedding_provider_id: number | null
  created_at: string
  updated_at: string
}

export interface DocumentList {
  total: number
  items: Document[]
}

// Chatbot
export interface Chatbot {
  id: number
  name: string
  description: string | null
  system_prompt: string | null
  llm_provider_id: number | null
  model: string | null
  temperature: number
  max_tokens: number
  use_knowledge_base: boolean
  top_k: number
  // 查询重写配置
  use_query_rewrite: boolean
  rewrite_provider_id: number | null
  rewrite_model: string | null
  created_at: string
  updated_at: string
  conversation_count: number
}

export interface ChatbotCreate {
  name: string
  description?: string
  system_prompt?: string
  llm_provider_id?: number
  model?: string
  temperature?: number
  max_tokens?: number
  use_knowledge_base?: boolean
  top_k?: number
  use_query_rewrite?: boolean
  rewrite_provider_id?: number
  rewrite_model?: string
}

export interface ChatbotList {
  total: number
  items: Chatbot[]
}

// Conversation
export interface Conversation {
  id: number
  chatbot_id: number
  title: string | null
  created_at: string
  updated_at: string
  message_count: number
  last_message: string | null
}

export interface ConversationList {
  total: number
  items: Conversation[]
}

// Message
export interface Message {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens_used: number | null
  sources: string | null
  created_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
}

// Test Response
export interface ProviderTestResponse {
  success: boolean
  message: string
  models?: string[]
  dimensions?: number
}

// Stats
export interface Stats {
  documents: {
    total: number
    completed: number
  }
  chatbots: number
  conversations: number
  providers: {
    llm: number
    embedding: number
  }
  vectorstore: {
    name: string
    count: number
  }
}

// Chat Log
export interface ChatLog {
  id: number
  conversation_id: number | null
  chatbot_id: number | null
  message_id: number | null
  llm_provider_id: number | null
  llm_provider_name: string | null
  model: string | null
  input_text: string
  output_text: string | null
  // 查询重写相关
  use_query_rewrite: boolean
  rewrite_time_ms: number | null
  rewritten_query: string | null
  // RAG相关
  use_rag: boolean
  rag_query_time_ms: number | null
  rag_results_count: number | null
  rag_results: string | null
  total_time_ms: number | null
  llm_time_ms: number | null
  input_tokens: number | null
  output_tokens: number | null
  status: string
  error_message: string | null
  created_at: string
  chatbot_name: string | null
  conversation_title: string | null
}

export interface ChatLogList {
  total: number
  items: ChatLog[]
}
