import client from './client'
import type {
  LLMProvider,
  LLMProviderCreate,
  EmbeddingProvider,
  EmbeddingProviderCreate,
  Document,
  DocumentList,
  Chatbot,
  ChatbotCreate,
  ChatbotList,
  Conversation,
  ConversationList,
  ConversationDetail,
  Message,
  ProviderTestResponse,
  Stats,
  ChatLog,
  ChatLogList,
} from './types'

// ============ LLM Providers ============

export const llmProviders = {
  list: () => client.get<LLMProvider[]>('/llm-providers').then((r) => r.data),
  get: (id: number) => client.get<LLMProvider>(`/llm-providers/${id}`).then((r) => r.data),
  create: (data: LLMProviderCreate) => client.post<LLMProvider>('/llm-providers', data).then((r) => r.data),
  update: (id: number, data: Partial<LLMProviderCreate>) => client.put<LLMProvider>(`/llm-providers/${id}`, data).then((r) => r.data),
  delete: (id: number) => client.delete(`/llm-providers/${id}`),
  test: (id: number) => client.post<ProviderTestResponse>(`/llm-providers/${id}/test`).then((r) => r.data),
}

// ============ Embedding Providers ============

export const embeddingProviders = {
  list: () => client.get<EmbeddingProvider[]>('/embedding-providers').then((r) => r.data),
  get: (id: number) => client.get<EmbeddingProvider>(`/embedding-providers/${id}`).then((r) => r.data),
  create: (data: EmbeddingProviderCreate) => client.post<EmbeddingProvider>('/embedding-providers', data).then((r) => r.data),
  update: (id: number, data: Partial<EmbeddingProviderCreate>) => client.put<EmbeddingProvider>(`/embedding-providers/${id}`, data).then((r) => r.data),
  delete: (id: number) => client.delete(`/embedding-providers/${id}`),
  test: (id: number) => client.post<ProviderTestResponse>(`/embedding-providers/${id}/test`).then((r) => r.data),
}

// ============ Documents ============

export const documents = {
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    client.get<DocumentList>('/documents', { params }).then((r) => r.data),
  get: (id: number) => client.get<Document>(`/documents/${id}`).then((r) => r.data),
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post<{ id: number; filename: string; status: string; message: string }>(
      '/documents/upload',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    ).then((r) => r.data)
  },
  delete: (id: number) => client.delete(`/documents/${id}`),
  reprocess: (id: number) => client.post<Document>(`/documents/${id}/reprocess`).then((r) => r.data),
}

// ============ Chatbots ============

export const chatbots = {
  list: (params?: { skip?: number; limit?: number }) =>
    client.get<ChatbotList>('/chatbots', { params }).then((r) => r.data),
  get: (id: number) => client.get<Chatbot>(`/chatbots/${id}`).then((r) => r.data),
  create: (data: ChatbotCreate) => client.post<Chatbot>('/chatbots', data).then((r) => r.data),
  update: (id: number, data: Partial<ChatbotCreate>) => client.put<Chatbot>(`/chatbots/${id}`, data).then((r) => r.data),
  delete: (id: number) => client.delete(`/chatbots/${id}`),
}

// ============ Conversations ============

export const conversations = {
  list: (chatbotId: number, params?: { skip?: number; limit?: number }) =>
    client.get<ConversationList>(`/chatbots/${chatbotId}/conversations`, { params }).then((r) => r.data),
  get: (id: number) => client.get<ConversationDetail>(`/conversations/${id}`).then((r) => r.data),
  create: (chatbotId: number, title?: string) =>
    client.post<Conversation>(`/chatbots/${chatbotId}/conversations`, { title }).then((r) => r.data),
  delete: (id: number) => client.delete(`/conversations/${id}`),
}

// ============ Chat ============

export const chat = {
  send: async function* (conversationId: number, message: string) {
    const response = await fetch(`/api/conversations/${conversationId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, stream: true }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Chat request failed')
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data)
            yield parsed.content
          } catch {
            // ignore parse errors
          }
        }
      }
    }
  },
}

// ============ Stats ============

export const stats = {
  get: () => client.get<Stats>('/stats').then((r) => r.data),
}

// ============ Chat Logs ============

export const chatLogs = {
  list: (params?: {
    conversation_id?: number
    message_id?: number
    chatbot_id?: number
    status?: string
    use_rag?: boolean
    skip?: number
    limit?: number
  }) => client.get<ChatLogList>('/chat-logs', { params }).then((r) => r.data),
  
  get: (id: number) => client.get<ChatLog>(`/chat-logs/${id}`).then((r) => r.data),
  
  getByConversation: (conversationId: number, limit: number = 50) =>
    client.get<ChatLogList>('/chat-logs', {
      params: { conversation_id: conversationId, limit }
    }).then((r) => r.data),
  
  getByMessageId: (messageId: number) =>
    client.get<ChatLogList>('/chat-logs', {
      params: { message_id: messageId, limit: 1 }
    }).then((r) => r.data.items[0] || null),
}

export type {
  LLMProvider,
  LLMProviderCreate,
  EmbeddingProvider,
  EmbeddingProviderCreate,
  Document,
  DocumentList,
  Chatbot,
  ChatbotCreate,
  ChatbotList,
  Conversation,
  ConversationList,
  ConversationDetail,
  Message,
  ProviderTestResponse,
  Stats,
  ChatLog,
  ChatLogList,
}

