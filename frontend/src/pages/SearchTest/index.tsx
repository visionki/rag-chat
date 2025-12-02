import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Search, Loader2, FileText, Zap } from 'lucide-react'
import clsx from 'clsx'
import { testSearch, getEmbeddingProviders } from '../../api/searchTest'
import type { SearchResult } from '../../api/searchTest'
import Button from '../../components/Button'

export default function SearchTestPage() {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(10)
  const [selectedProviderId, setSelectedProviderId] = useState<number | undefined>()
  const [results, setResults] = useState<SearchResult[]>([])
  const [searchInfo, setSearchInfo] = useState<{
    provider: string
    timeMs: number
  } | null>(null)

  // 获取嵌入模型列表
  const { data: providers } = useQuery({
    queryKey: ['embedding-providers'],
    queryFn: async () => {
      const res = await getEmbeddingProviders()
      return res.data
    },
  })

  // 设置默认选中的提供商
  useEffect(() => {
    if (providers && !selectedProviderId) {
      const defaultProvider = providers.find((p) => p.is_default)
      if (defaultProvider) {
        setSelectedProviderId(defaultProvider.id)
      }
    }
  }, [providers, selectedProviderId])

  // 搜索
  const searchMutation = useMutation({
    mutationFn: testSearch,
    onSuccess: (response) => {
      setResults(response.data.results)
      setSearchInfo({
        provider: response.data.embedding_provider,
        timeMs: response.data.total_time_ms,
      })
    },
  })

  const handleSearch = () => {
    if (!query.trim()) return
    searchMutation.mutate({
      query: query.trim(),
      top_k: topK,
      embedding_provider_id: selectedProviderId,
    })
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="h-full overflow-hidden flex flex-col bg-gray-900">
      {/* 头部 */}
      <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Search className="w-6 h-6 text-purple-400" />
              </div>
              检索测试
            </h1>
            <p className="text-gray-400 mt-1">测试向量检索功能，查看命中的文档片段</p>
          </div>
        </div>
      </div>

      {/* 主内容区 */}
      <div className="flex-1 overflow-auto px-8 py-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* 搜索配置 */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
            <div className="space-y-4">
              {/* 查询输入 */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  查询关键词
                </label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="输入要搜索的关键词..."
                  className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                />
              </div>

              {/* 配置选项 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 结果数量 */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    返回结果数量
                  </label>
                  <input
                    type="number"
                    value={topK}
                    onChange={(e) => setTopK(Math.max(1, Math.min(50, parseInt(e.target.value) || 10)))}
                    min="1"
                    max="50"
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">范围: 1-50</p>
                </div>

                {/* 嵌入模型选择 */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    嵌入模型
                  </label>
                  <select
                    value={selectedProviderId || ''}
                    onChange={(e) => setSelectedProviderId(e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                  >
                    {providers?.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name} ({provider.model})
                        {provider.is_default ? ' [默认]' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* 搜索按钮 */}
              <div>
                <Button
                  onClick={handleSearch}
                  disabled={!query.trim() || searchMutation.isPending}
                  className="w-full"
                >
                  {searchMutation.isPending ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      搜索中...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      开始搜索
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* 搜索信息 */}
          {searchInfo && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-4">
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span className="text-gray-400">耗时:</span>
                  <span className="text-white font-medium">{searchInfo.timeMs}ms</span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <span className="text-gray-400">模型:</span>
                  <span className="text-white font-medium">{searchInfo.provider}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-400">结果数:</span>
                  <span className="text-white font-medium">{results.length}</span>
                </div>
              </div>
            </div>
          )}

          {/* 搜索结果 */}
          {results.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">检索结果</h2>
              {results.map((result, index) => (
                <div
                  key={`${result.document_id}-${result.chunk_index}-${index}`}
                  className="bg-gray-800 rounded-xl border border-gray-700 p-6 hover:border-purple-500/50 transition-colors"
                >
                  {/* 结果头部 */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-lg font-bold text-purple-400">
                          #{index + 1}
                        </span>
                        <div className="flex items-center gap-2 text-white">
                          <FileText className="w-4 h-4" />
                          <span className="font-medium">{result.filename}</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          chunk {result.chunk_index}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">相似度:</span>
                      <div
                        className={clsx(
                          'px-3 py-1 rounded-full text-sm font-medium',
                          result.score > 0.8
                            ? 'bg-green-500/20 text-green-400'
                            : result.score > 0.6
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-gray-500/20 text-gray-400'
                        )}
                      >
                        {(result.score * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* 文档内容 */}
                  <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                    <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {result.content}
                    </p>
                  </div>

                  {/* 元数据 */}
                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <details className="text-xs">
                        <summary className="text-gray-400 cursor-pointer hover:text-gray-300">
                          元数据
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-900 rounded text-gray-400 overflow-x-auto">
                          {JSON.stringify(result.metadata, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* 空状态 */}
          {!searchMutation.isPending && results.length === 0 && searchInfo && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
              <div className="text-gray-500 text-sm">
                未找到匹配的文档片段
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

