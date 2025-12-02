import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Clock,
  Database,
  Zap,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Search,
  FileText,
} from 'lucide-react'
import clsx from 'clsx'
import client from '../../api/client'
import Select from '../../components/Select'
import EmptyState from '../../components/EmptyState'

interface ChatLog {
  id: number
  conversation_id: number | null
  chatbot_id: number | null
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

interface ChatLogStats {
  total_requests: number
  success_count: number
  error_count: number
  avg_total_time_ms: number | null
  avg_rag_time_ms: number | null
  avg_llm_time_ms: number | null
  total_input_tokens: number
  total_output_tokens: number
}

export default function LogsPage() {
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [filters, setFilters] = useState({
    status: '',
    use_rag: '',
  })

  // 获取日志列表
  const { data: logsData, isLoading } = useQuery({
    queryKey: ['chat-logs', filters],
    queryFn: async () => {
      const params: Record<string, string> = {}
      if (filters.status) params.status = filters.status
      if (filters.use_rag) params.use_rag = filters.use_rag
      const res = await client.get<{ total: number; items: ChatLog[] }>('/chat-logs', { params })
      return res.data
    },
  })

  // 获取统计信息
  const { data: stats } = useQuery({
    queryKey: ['chat-logs-stats'],
    queryFn: async () => {
      const res = await client.get<ChatLogStats>('/chat-logs/stats')
      return res.data
    },
  })

  const formatTime = (ms: number | null) => {
    if (ms === null) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  return (
    <div className="h-full flex flex-col">
      {/* 顶部栏 */}
      <div className="px-6 py-4 border-b border-dark-800">
        <h1 className="text-xl font-semibold text-dark-100">请求日志</h1>
        <p className="text-sm text-dark-500 mt-1">查看所有问答请求的详细日志</p>
      </div>

      {/* 统计卡片 */}
      <div className="px-6 py-4 grid grid-cols-5 gap-4">
        <StatCard
          label="总请求"
          value={stats?.total_requests || 0}
          icon={Database}
        />
        <StatCard
          label="成功"
          value={stats?.success_count || 0}
          icon={CheckCircle}
          color="text-green-400"
        />
        <StatCard
          label="失败"
          value={stats?.error_count || 0}
          icon={XCircle}
          color="text-red-400"
        />
        <StatCard
          label="平均响应"
          value={formatTime(stats?.avg_total_time_ms || null)}
          icon={Clock}
        />
        <StatCard
          label="平均RAG"
          value={formatTime(stats?.avg_rag_time_ms || null)}
          icon={Zap}
        />
      </div>

      {/* 筛选栏 */}
      <div className="px-6 py-3 border-b border-dark-800 flex items-center gap-4">
        <Select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          options={[
            { value: '', label: '全部状态' },
            { value: 'success', label: '成功' },
            { value: 'error', label: '失败' },
          ]}
        />
        <Select
          value={filters.use_rag}
          onChange={(e) => setFilters({ ...filters, use_rag: e.target.value })}
          options={[
            { value: '', label: '全部类型' },
            { value: 'true', label: '使用RAG' },
            { value: 'false', label: '未使用RAG' },
          ]}
        />
      </div>

      {/* 日志列表 */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
          </div>
        ) : logsData?.items.length === 0 ? (
          <EmptyState
            icon={Search}
            title="暂无日志"
            description="开始对话后，这里会显示请求日志"
          />
        ) : (
          <div className="space-y-3">
            {logsData?.items.map((log) => (
              <LogCard
                key={log.id}
                log={log}
                expanded={expandedId === log.id}
                onToggle={() => setExpandedId(expandedId === log.id ? null : log.id)}
                formatTime={formatTime}
                formatDate={formatDate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color = 'text-primary-400',
}: {
  label: string
  value: number | string
  icon: React.ElementType
  color?: string
}) {
  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-dark-800 rounded-lg flex items-center justify-center">
          <Icon className={clsx('w-5 h-5', color)} />
        </div>
        <div>
          <p className="text-xl font-semibold text-dark-100">{value}</p>
          <p className="text-sm text-dark-500">{label}</p>
        </div>
      </div>
    </div>
  )
}

function LogCard({
  log,
  expanded,
  onToggle,
  formatTime,
  formatDate,
}: {
  log: ChatLog
  expanded: boolean
  onToggle: () => void
  formatTime: (ms: number | null) => string
  formatDate: (date: string) => string
}) {
  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden">
      {/* 摘要行 */}
      <div
        className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-dark-800/50"
        onClick={onToggle}
      >
        <div className="flex items-center gap-4 min-w-0 flex-1">
          {/* 状态 */}
          <div
            className={clsx(
              'w-2 h-2 rounded-full flex-shrink-0',
              log.status === 'success' ? 'bg-green-400' : 'bg-red-400'
            )}
          />

          {/* 时间 */}
          <span className="text-xs text-dark-500 flex-shrink-0 w-36">
            {formatDate(log.created_at)}
          </span>

          {/* 模型 */}
          <span className="text-xs text-dark-400 bg-dark-800 px-2 py-0.5 rounded flex-shrink-0">
            {log.model || 'N/A'}
          </span>

          {/* 查询重写标记 */}
          {log.use_query_rewrite && (
            <span className="text-xs text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded flex-shrink-0">
              重写
            </span>
          )}

          {/* RAG标记 */}
          {log.use_rag && (
            <span className="text-xs text-primary-400 bg-primary-400/10 px-2 py-0.5 rounded flex-shrink-0">
              RAG
            </span>
          )}

          {/* 输入预览 */}
          <span className="text-sm text-dark-200 truncate">
            {log.input_text}
          </span>
        </div>

        {/* 右侧信息 */}
        <div className="flex items-center gap-4 flex-shrink-0">
          <span className="text-xs text-dark-500">
            {formatTime(log.total_time_ms)}
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-dark-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-dark-500" />
          )}
        </div>
      </div>

      {/* 展开详情 */}
      {expanded && (
        <div className="border-t border-dark-800 p-4 space-y-4 animate-fade-in">
          {/* 性能指标 */}
          <div className="grid grid-cols-5 gap-4">
            <MetricItem label="总耗时" value={formatTime(log.total_time_ms)} />
            <MetricItem label="重写耗时" value={log.use_query_rewrite ? formatTime(log.rewrite_time_ms) : '-'} />
            <MetricItem label="LLM耗时" value={formatTime(log.llm_time_ms)} />
            <MetricItem label="RAG耗时" value={formatTime(log.rag_query_time_ms)} />
            <MetricItem label="检索结果" value={log.rag_results_count?.toString() || '-'} />
          </div>

          {/* 输入 */}
          <div>
            <h4 className="text-xs font-medium text-dark-400 mb-2">输入</h4>
            <div className="bg-dark-950 rounded-lg p-3 text-sm text-dark-200 whitespace-pre-wrap">
              {log.input_text}
            </div>
          </div>

          {/* 重写后的查询 */}
          {log.use_query_rewrite && log.rewritten_query && (
            <div>
              <h4 className="text-xs font-medium text-orange-400 mb-2">重写后的查询</h4>
              <div className="bg-orange-500/5 border border-orange-500/20 rounded-lg p-3 text-sm text-orange-200 whitespace-pre-wrap">
                {log.rewritten_query}
              </div>
            </div>
          )}

          {/* 输出 */}
          <div>
            <h4 className="text-xs font-medium text-dark-400 mb-2">输出</h4>
            <div className="bg-dark-950 rounded-lg p-3 text-sm text-dark-200 whitespace-pre-wrap max-h-64 overflow-y-auto">
              {log.output_text || '(无输出)'}
            </div>
          </div>

          {/* RAG结果 */}
          {log.rag_results && (
            <div>
              <h4 className="text-xs font-medium text-dark-400 mb-2">RAG检索结果</h4>
              <RagResultsExpand results={log.rag_results} />
            </div>
          )}

          {/* 错误信息 */}
          {log.error_message && (
            <div>
              <h4 className="text-xs font-medium text-red-400 mb-2">错误信息</h4>
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-300">
                {log.error_message}
              </div>
            </div>
          )}

          {/* 元信息 */}
          <div className="flex flex-wrap gap-4 text-xs text-dark-500">
            <span>Provider: {log.llm_provider_name || 'N/A'}</span>
            <span>Bot: {log.chatbot_name || 'N/A'}</span>
            <span>会话: {log.conversation_title || 'N/A'}</span>
          </div>
        </div>
      )}
    </div>
  )
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-dark-800 rounded-lg p-3">
      <p className="text-xs text-dark-500 mb-1">{label}</p>
      <p className="text-sm font-medium text-dark-200">{value}</p>
    </div>
  )
}

function RagResultsExpand({ results }: { results: string }) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)

  try {
    const parsed = JSON.parse(results)
    return (
      <div className="space-y-2">
        {parsed.map((item: any, index: number) => {
          const isExpanded = expandedIndex === index
          return (
            <div
              key={index}
              className="bg-dark-950 rounded-lg border border-dark-800 overflow-hidden"
            >
              {/* 可点击的头部 */}
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full p-3 flex items-center justify-between hover:bg-dark-900 transition-colors text-left"
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <FileText className="w-4 h-4 text-dark-500 flex-shrink-0" />
                  <span className="text-dark-200 font-medium truncate text-sm">
                    {item.filename || '未知文件'}
                  </span>
                  {item.chunk_index !== undefined && (
                    <span className="text-dark-600 text-xs">#{item.chunk_index}</span>
                  )}
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-primary-400 text-xs font-medium">
                    相似度: {(item.score * 100).toFixed(1)}%
                  </span>
                  <ChevronDown
                    className={clsx(
                      'w-4 h-4 text-dark-500 transition-transform',
                      isExpanded && 'rotate-180'
                    )}
                  />
                </div>
              </button>

              {/* 展开的内容 */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-0 border-t border-dark-800 animate-fade-in">
                  <p className="text-dark-300 text-sm leading-relaxed whitespace-pre-wrap mt-3">
                    {item.content}
                  </p>
                </div>
              )}

              {/* 折叠时的预览 */}
              {!isExpanded && (
                <div className="px-3 pb-3 pt-0">
                  <p className="text-dark-500 text-xs line-clamp-2">{item.content}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  } catch {
    return (
      <div className="bg-dark-950 rounded-lg p-3 text-sm text-dark-300 max-h-48 overflow-y-auto">
        <pre className="whitespace-pre-wrap text-xs">{results}</pre>
      </div>
    )
  }
}


