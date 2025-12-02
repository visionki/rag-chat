import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
} from 'lucide-react'
import clsx from 'clsx'
import { documents } from '../../api'
import Button from '../../components/Button'
import EmptyState from '../../components/EmptyState'

const statusConfig = {
  pending: {
    icon: Clock,
    text: '等待处理',
    color: 'text-yellow-400',
    bg: 'bg-yellow-400/10',
  },
  processing: {
    icon: Loader2,
    text: '处理中',
    color: 'text-blue-400',
    bg: 'bg-blue-400/10',
  },
  completed: {
    icon: CheckCircle,
    text: '已完成',
    color: 'text-green-400',
    bg: 'bg-green-400/10',
  },
  failed: {
    icon: XCircle,
    text: '失败',
    color: 'text-red-400',
    bg: 'bg-red-400/10',
  },
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function DocumentsPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  // 获取文档列表
  const { data: documentList, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documents.list(),
    refetchInterval: 5000, // 自动刷新
  })

  // 上传文档
  const uploadMutation = useMutation({
    mutationFn: (file: File) => documents.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  // 删除文档
  const deleteMutation = useMutation({
    mutationFn: (id: number) => documents.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  // 重新处理
  const reprocessMutation = useMutation({
    mutationFn: (id: number) => documents.reprocess(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files?.length) return

    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        await uploadMutation.mutateAsync(file)
      }
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* 顶部栏 */}
      <div className="px-6 py-4 border-b border-dark-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-dark-100">文档管理</h1>
          <p className="text-sm text-dark-500 mt-1">
            上传文档构建知识库，支持 TXT、Markdown、PDF、Word 格式
          </p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".txt,.md,.markdown,.pdf,.docx"
            onChange={handleFileChange}
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            loading={uploading}
          >
            <Upload className="w-4 h-4" />
            上传文档
          </Button>
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
          </div>
        ) : documentList?.items.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="还没有文档"
            description="上传文档来构建你的知识库"
            action={
              <Button onClick={() => fileInputRef.current?.click()}>
                <Upload className="w-4 h-4" />
                上传文档
              </Button>
            }
          />
        ) : (
          <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-800">
                  <th className="text-left px-4 py-3 text-sm font-medium text-dark-400">
                    文件名
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-dark-400">
                    类型
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-dark-400">
                    大小
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-dark-400">
                    分块数
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-dark-400">
                    状态
                  </th>
                  <th className="text-right px-4 py-3 text-sm font-medium text-dark-400">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody>
                {documentList?.items.map((doc) => {
                  const status = statusConfig[doc.status]
                  const StatusIcon = status.icon

                  return (
                    <tr
                      key={doc.id}
                      className="border-b border-dark-800 last:border-b-0 hover:bg-dark-800/50"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-dark-500" />
                          <div>
                            <p className="text-sm text-dark-100 font-medium">
                              {doc.filename}
                            </p>
                            {doc.error_message && (
                              <p className="text-xs text-red-400 mt-0.5">
                                {doc.error_message}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-dark-400 uppercase">
                          {doc.file_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-dark-400">
                          {formatFileSize(doc.file_size)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-sm text-dark-400">
                          {doc.chunk_count}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs',
                            status.bg,
                            status.color
                          )}
                        >
                          <StatusIcon
                            className={clsx(
                              'w-3.5 h-3.5',
                              doc.status === 'processing' && 'animate-spin'
                            )}
                          />
                          {status.text}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          {doc.status === 'failed' && (
                            <button
                              className="p-1.5 text-dark-400 hover:text-dark-200 hover:bg-dark-700 rounded-lg transition-colors"
                              onClick={() => reprocessMutation.mutate(doc.id)}
                              title="重新处理"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-700 rounded-lg transition-colors"
                            onClick={() => deleteMutation.mutate(doc.id)}
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}


