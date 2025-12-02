import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Plus, Trash2, MessageSquare, Bot, Clock, Zap, Database, ChevronRight, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import clsx from 'clsx'
import { chatbots, conversations, chat, chatLogs } from '../../api'
import type { Message } from '../../api'
import Button from '../../components/Button'
import EmptyState from '../../components/EmptyState'
import MessageLogModal from '../../components/MessageLogModal'

export default function ChatPage() {
  const { chatbotId, conversationId } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [selectedLogMessageId, setSelectedLogMessageId] = useState<number | null>(null)
  
  // 追踪当前加载的会话ID，避免切换会话时数据错乱
  const loadedConversationIdRef = useRef<string | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // 获取Chatbot列表
  const { data: chatbotList } = useQuery({
    queryKey: ['chatbots'],
    queryFn: () => chatbots.list(),
  })

  // 获取会话列表
  const { data: conversationList } = useQuery({
    queryKey: ['conversations', chatbotId],
    queryFn: () => conversations.list(Number(chatbotId)),
    enabled: !!chatbotId,
  })

  // 自动跳转到最后一个 Bot（如果没有选择）
  useEffect(() => {
    if (!chatbotId && chatbotList?.items && chatbotList.items.length > 0) {
      // 跳转到最后创建的 bot（列表末尾，或按 ID 最大的）
      const lastBot = chatbotList.items[chatbotList.items.length - 1]
      navigate(`/chat/${lastBot.id}`, { replace: true })
    }
  }, [chatbotId, chatbotList, navigate])

  // 自动跳转到最后一个会话（如果有 Bot 但没有选择会话）
  useEffect(() => {
    if (chatbotId && !conversationId && conversationList?.items && conversationList.items.length > 0) {
      // 跳转到最后一个会话（最近的会话通常在最前面）
      const lastConversation = conversationList.items[0]
      navigate(`/chat/${chatbotId}/${lastConversation.id}`, { replace: true })
    }
  }, [chatbotId, conversationId, conversationList, navigate])

  // 获取当前会话详情
  const { data: conversationDetail } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => conversations.get(Number(conversationId)),
    enabled: !!conversationId,
  })

  // 加载会话消息 - 仅在切换会话或初次加载时更新
  useEffect(() => {
    // 只在以下情况更新消息：
    // 1. 切换到新的会话（conversationId 变化）
    // 2. 不在流式传输中（避免覆盖正在生成的内容）
    if (conversationDetail?.messages && !isStreaming) {
      // 检查是否是切换到新会话
      if (loadedConversationIdRef.current !== conversationId) {
        setMessages(conversationDetail.messages)
        loadedConversationIdRef.current = conversationId || null
      }
    }
  }, [conversationDetail, conversationId, isStreaming])

  // 切换会话时重置状态
  useEffect(() => {
    if (conversationId !== loadedConversationIdRef.current) {
      // 切换会话时清空消息，等待新数据加载
      setMessages([])
      setStreamingContent('')
      loadedConversationIdRef.current = null
    }
  }, [conversationId])

  // 滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  // 创建新会话
  const createConversation = useMutation({
    mutationFn: (botId: number) => conversations.create(botId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['conversations', chatbotId] })
      navigate(`/chat/${chatbotId}/${data.id}`)
    },
  })

  // 删除会话
  const deleteConversation = useMutation({
    mutationFn: (id: number) => conversations.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations', chatbotId] })
      if (conversationId) {
        navigate(`/chat/${chatbotId}`)
      }
    },
  })

  // 发送消息
  const sendMessage = useCallback(async () => {
    if (!input.trim() || !conversationId || isStreaming) return

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: Number(conversationId),
      role: 'user',
      content: input.trim(),
      tokens_used: null,
      sources: null,
      created_at: new Date().toISOString(),
    }

    // 保存当前输入并立即清空，避免重复发送
    const messageContent = input.trim()
    setInput('')
    setMessages((prev) => [...prev, userMessage])
    setIsStreaming(true)
    setStreamingContent('')

    try {
      let fullContent = ''
      for await (const chunk of chat.send(Number(conversationId), messageContent)) {
        fullContent += chunk
        setStreamingContent(fullContent)
      }

      // 流式响应完成，先添加临时 AI 消息到 messages，再清空流式内容
      // 这样可以避免界面闪烁
      const tempAssistantMessage: Message = {
        id: Date.now() + 1, // 临时 ID
        conversation_id: Number(conversationId),
        role: 'assistant',
        content: fullContent,
        tokens_used: null,
        sources: null,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, tempAssistantMessage])
      setStreamingContent('')

      // 后台静默刷新会话详情获取真实的消息 ID（用于日志关联）
      // 使用 functional update 只更新 ID 等元数据，保持内容不变，避免闪烁
      const updatedConversation = await conversations.get(Number(conversationId))
      if (updatedConversation?.messages) {
        // 静默替换消息列表，内容相同所以不会有视觉变化
        setMessages(updatedConversation.messages)
        loadedConversationIdRef.current = conversationId || null
      }

      // 刷新会话列表（更新标题和最后消息预览）
      queryClient.invalidateQueries({ queryKey: ['conversations', chatbotId] })
    } catch (error) {
      console.error('Chat error:', error)
      // 发生错误时，移除刚添加的用户消息
      setMessages((prev) => prev.filter(m => m.id !== userMessage.id))
    } finally {
      setIsStreaming(false)
    }
  }, [input, conversationId, isStreaming, chatbotId, queryClient])

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="h-full flex">
      {/* 左侧会话列表 */}
      <div className="w-64 bg-dark-900 border-r border-dark-800 flex flex-col">
        {/* Chatbot选择 */}
        <div className="p-4 border-b border-dark-800">
          <select
            value={chatbotId || ''}
            onChange={(e) => navigate(`/chat/${e.target.value}`)}
            className="w-full px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-dark-100 text-sm"
          >
            <option value="">选择机器人</option>
            {chatbotList?.items.map((bot) => (
              <option key={bot.id} value={bot.id}>
                {bot.name}
              </option>
            ))}
          </select>
        </div>

        {/* 新建会话按钮 */}
        {chatbotId && (
          <div className="p-3">
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={() => createConversation.mutate(Number(chatbotId))}
              loading={createConversation.isPending}
            >
              <Plus className="w-4 h-4" />
              新建会话
            </Button>
          </div>
        )}

        {/* 会话列表 */}
        <div className="flex-1 overflow-y-auto">
          {conversationList?.items.map((conv) => (
            <div
              key={conv.id}
              className={clsx(
                'group px-3 py-2 mx-2 rounded-lg cursor-pointer transition-colors',
                'hover:bg-dark-800',
                conversationId === String(conv.id) && 'bg-dark-800'
              )}
              onClick={() => navigate(`/chat/${chatbotId}/${conv.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="w-4 h-4 text-dark-500 flex-shrink-0" />
                  <span className="text-sm text-dark-200 truncate">
                    {conv.title || '新会话'}
                  </span>
                </div>
                <button
                  className="opacity-0 group-hover:opacity-100 p-1 text-dark-500 hover:text-red-400 transition-all"
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteConversation.mutate(conv.id)
                  }}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              {conv.last_message && (
                <p className="text-xs text-dark-500 truncate mt-1 pl-6">
                  {conv.last_message}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 右侧聊天区 */}
      <div className="flex-1 flex flex-col">
        {conversationId ? (
          <>
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={clsx(
                    'flex gap-3 animate-fade-in',
                    msg.role === 'user' && 'flex-row-reverse'
                  )}
                >
                  {/* 头像 */}
                  <div
                    className={clsx(
                      'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                      msg.role === 'user'
                        ? 'bg-primary-600'
                        : 'bg-dark-700'
                    )}
                  >
                    {msg.role === 'user' ? (
                      <span className="text-white text-sm font-medium">U</span>
                    ) : (
                      <Bot className="w-4 h-4 text-dark-300" />
                    )}
                  </div>

                  {/* 消息内容 */}
                  <div className="max-w-[70%]">
                  <div
                    className={clsx(
                        'rounded-2xl px-4 py-2.5',
                      msg.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-dark-800 text-dark-100'
                    )}
                  >
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="markdown-body">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                      </div>
                      )}
                    </div>
                    {/* AI回复底部的日志简要栏 */}
                    {msg.role === 'assistant' && (
                      <MessageLogBar
                        messageId={msg.id}
                        onViewDetail={() => setSelectedLogMessageId(msg.id)}
                      />
                    )}
                  </div>
                </div>
              ))}

              {/* 流式响应 */}
              {isStreaming && streamingContent && (
                <div className="flex gap-3 animate-fade-in">
                  <div className="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-dark-300" />
                  </div>
                  <div className="max-w-[70%] rounded-2xl px-4 py-2.5 bg-dark-800 text-dark-100">
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}

              {/* 加载指示器 */}
              {isStreaming && !streamingContent && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-dark-300" />
                  </div>
                  <div className="bg-dark-800 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-dark-500 rounded-full animate-pulse" />
                      <span className="w-2 h-2 bg-dark-500 rounded-full animate-pulse delay-100" />
                      <span className="w-2 h-2 bg-dark-500 rounded-full animate-pulse delay-200" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* 输入区 */}
            <div className="p-4 border-t border-dark-800">
              <div className="flex gap-3 items-end">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入消息..."
                  rows={1}
                  className="flex-1 px-4 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-primary-500 resize-none"
                  style={{ maxHeight: '120px' }}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!input.trim() || isStreaming}
                  className="h-12 w-12 !p-0"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
            </div>

            {/* 消息日志弹窗 */}
            <MessageLogModal
              messageId={selectedLogMessageId || 0}
              isOpen={!!selectedLogMessageId}
              onClose={() => setSelectedLogMessageId(null)}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              icon={MessageSquare}
              title={chatbotId ? '选择或创建一个会话' : '请先选择一个机器人'}
              description={
                chatbotId
                  ? '点击左侧"新建会话"开始对话'
                  : '在左上角下拉菜单中选择一个机器人'
              }
            />
          </div>
        )}
      </div>
    </div>
  )
}

// 消息日志简要栏组件
function MessageLogBar({ messageId, onViewDetail }: { messageId: number; onViewDetail: () => void }) {
  const { data: log, isLoading } = useQuery({
    queryKey: ['chat-log', 'message', messageId],
    queryFn: () => chatLogs.getByMessageId(messageId),
    staleTime: 60000, // 1分钟内不重新请求
  })

  const formatTime = (ms: number | null) => {
    if (ms === null) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // 未找到日志或加载中时显示简单的按钮
  if (isLoading) {
    return (
      <div className="flex items-center mt-1.5 ml-1 h-5">
        <div className="w-3 h-3 border border-dark-600 border-t-dark-400 rounded-full animate-spin" />
      </div>
    )
  }

  if (!log) {
    return null // 没有日志记录时不显示
  }

  return (
    <button
      onClick={onViewDetail}
      className="flex items-center gap-3 mt-1.5 ml-1 px-2 py-1 rounded-lg text-xs text-dark-500 hover:text-dark-300 hover:bg-dark-800/50 transition-colors group"
    >
      {/* 总耗时 */}
      <span className="flex items-center gap-1">
        <Clock className="w-3 h-3" />
        {formatTime(log.total_time_ms)}
      </span>

      {/* 查询重写耗时（如果有） */}
      {log.use_query_rewrite && (
        <span className="flex items-center gap-1 text-orange-500/70">
          <RefreshCw className="w-3 h-3" />
          {formatTime(log.rewrite_time_ms)}
        </span>
      )}

      {/* LLM 耗时 */}
      <span className="flex items-center gap-1 text-yellow-500/70">
        <Zap className="w-3 h-3" />
        {formatTime(log.llm_time_ms)}
      </span>

      {/* RAG 耗时（如果有） */}
      {log.use_rag && (
        <span className="flex items-center gap-1 text-blue-500/70">
          <Database className="w-3 h-3" />
          {formatTime(log.rag_query_time_ms)}
          {log.rag_results_count !== null && (
            <span className="text-dark-600">({log.rag_results_count})</span>
          )}
        </span>
      )}

      {/* 查看详情箭头 */}
      <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  )
}

