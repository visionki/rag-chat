import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  X,
  Clock,
  Zap,
  Database,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  FileText,
  RefreshCw,
} from 'lucide-react'
import clsx from 'clsx'
import { chatLogs } from '../api'
import type { ChatLog } from '../api'

interface MessageLogModalProps {
  messageId: number
  isOpen: boolean
  onClose: () => void
}

export default function MessageLogModal({ messageId, isOpen, onClose }: MessageLogModalProps) {
  const { data: log, isLoading, error } = useQuery({
    queryKey: ['chat-log', 'message', messageId],
    queryFn: () => chatLogs.getByMessageId(messageId),
    enabled: isOpen && !!messageId,
  })

  const formatTime = (ms: number | null) => {
    if (ms === null) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  if (!isOpen) return null

  return (
    <>
      {/* 遮罩 */}
      <div
        className="fixed inset-0 bg-black/50 z-50 animate-fade-in"
        onClick={onClose}
      />

      {/* 弹窗 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-dark-900 border border-dark-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden pointer-events-auto animate-scale-in"
          onClick={(e) => e.stopPropagation()}
        >
          {/* 头部 */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-dark-800 bg-dark-850">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-primary-400" />
              <h3 className="font-semibold text-dark-100">消息日志详情</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-dark-400 hover:text-dark-200 hover:bg-dark-800 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* 内容 */}
          <div className="p-5 overflow-y-auto max-h-[calc(90vh-60px)]">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center h-32 text-red-400">
                <XCircle className="w-8 h-8 mb-2" />
                <p className="text-sm">加载失败</p>
              </div>
            ) : !log ? (
              <div className="flex flex-col items-center justify-center h-32 text-dark-500">
                <Database className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">未找到日志记录</p>
                <p className="text-xs mt-1 text-dark-600">该消息可能是历史数据</p>
              </div>
            ) : (
              <LogContent log={log} formatTime={formatTime} formatDate={formatDate} />
            )}
          </div>
        </div>
      </div>
    </>
  )
}

function LogContent({
  log,
  formatTime,
  formatDate,
}: {
  log: ChatLog
  formatTime: (ms: number | null) => string
  formatDate: (date: string) => string
}) {
  return (
    <div className="space-y-4">
      {/* 状态和基本信息 */}
      <div className="flex items-center gap-3">
        {log.status === 'success' ? (
          <div className="flex items-center gap-1.5 text-green-400 bg-green-400/10 px-2.5 py-1 rounded-full">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">成功</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-red-400 bg-red-400/10 px-2.5 py-1 rounded-full">
            <XCircle className="w-4 h-4" />
            <span className="text-sm font-medium">失败</span>
          </div>
        )}
        <span className="text-xs text-dark-500">{formatDate(log.created_at)}</span>
        <span className="text-xs text-dark-500">#{log.id}</span>
      </div>

      {/* 性能指标 */}
      <div className={`grid gap-2 ${log.use_query_rewrite ? 'grid-cols-5' : 'grid-cols-4'}`}>
        <MetricCard
          icon={Clock}
          label="总耗时"
          value={formatTime(log.total_time_ms)}
        />
        {log.use_query_rewrite && (
          <MetricCard
            icon={RefreshCw}
            label="重写"
            value={formatTime(log.rewrite_time_ms)}
            color="text-orange-400"
          />
        )}
        <MetricCard
          icon={Zap}
          label="LLM"
          value={formatTime(log.llm_time_ms)}
          color="text-yellow-400"
        />
        <MetricCard
          icon={Database}
          label="RAG"
          value={formatTime(log.rag_query_time_ms)}
          color="text-blue-400"
        />
        <MetricCard
          icon={Database}
          label="检索数"
          value={log.rag_results_count?.toString() || '-'}
          color="text-purple-400"
        />
      </div>

      {/* 模型信息 */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs bg-dark-800 text-dark-300 px-2 py-1 rounded">
          Provider: {log.llm_provider_name || 'N/A'}
        </span>
        <span className="text-xs bg-dark-800 text-dark-300 px-2 py-1 rounded">
          Model: {log.model || 'N/A'}
        </span>
        {log.use_rag && (
          <span className="text-xs bg-primary-400/10 text-primary-400 px-2 py-1 rounded">
            使用RAG
          </span>
        )}
        {log.use_query_rewrite && (
          <span className="text-xs bg-orange-400/10 text-orange-400 px-2 py-1 rounded">
            查询重写
          </span>
        )}
      </div>

      {/* 用户输入 */}
      <div>
        <h4 className="text-xs font-medium text-dark-400 mb-1.5 flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
          用户输入
        </h4>
        <div className="bg-dark-950 rounded-lg p-3 text-sm text-dark-200 whitespace-pre-wrap max-h-20 overflow-y-auto">
          {log.input_text}
        </div>
      </div>

      {/* 重写后的查询 */}
      {log.rewritten_query && (
        <div>
          <h4 className="text-xs font-medium text-dark-400 mb-1.5 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
            重写后的查询
            <span className="text-dark-600 ml-1">({formatTime(log.rewrite_time_ms)})</span>
          </h4>
          <div className="bg-orange-500/5 border border-orange-500/20 rounded-lg p-3 text-sm text-orange-200 whitespace-pre-wrap">
            {log.rewritten_query}
          </div>
        </div>
      )}

      {/* RAG检索结果 */}
      {log.rag_results && (
        <div className="flex-1">
          <h4 className="text-xs font-medium text-dark-400 mb-1.5 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full"></span>
            RAG检索结果 ({log.rag_results_count || 0} 条)
          </h4>
          <div className="text-sm text-dark-300 max-h-[50vh] overflow-y-auto">
            <RagResults results={log.rag_results} />
          </div>
        </div>
      )}

      {/* 错误信息 */}
      {log.error_message && (
        <div>
          <h4 className="text-xs font-medium text-red-400 mb-1.5">错误信息</h4>
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-300">
            {log.error_message}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  color = 'text-dark-400',
}: {
  icon: React.ElementType
  label: string
  value: string
  color?: string
}) {
  return (
    <div className="bg-dark-800 rounded-lg p-2.5 text-center">
      <Icon className={clsx('w-4 h-4 mx-auto mb-1', color)} />
      <p className="text-sm text-dark-200 font-medium">{value}</p>
      <p className="text-[10px] text-dark-500">{label}</p>
    </div>
  )
}

function RagResults({ results }: { results: string }) {
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
              className="bg-dark-900/50 rounded-lg border border-dark-800 overflow-hidden"
            >
              {/* 可点击的头部 */}
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full p-3 flex items-center justify-between hover:bg-dark-800/30 transition-colors text-left"
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
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-primary-400 text-xs font-medium">
                    {(item.score * 100).toFixed(1)}%
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
    return <pre className="whitespace-pre-wrap text-xs">{results}</pre>
  }
}

