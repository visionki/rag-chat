import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Server, Plus, Trash2, Edit, Zap, Database } from 'lucide-react'
import clsx from 'clsx'
import { llmProviders, embeddingProviders, stats } from '../../api'
import type {
  LLMProvider,
  LLMProviderCreate,
  EmbeddingProvider,
  EmbeddingProviderCreate,
} from '../../api'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Input from '../../components/Input'
import Select from '../../components/Select'

type TabType = 'llm' | 'embedding'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('llm')

  // 获取统计信息
  const { data: systemStats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => stats.get(),
  })

  return (
    <div className="h-full flex flex-col">
      {/* 顶部栏 */}
      <div className="px-6 py-4 border-b border-dark-800">
        <h1 className="text-xl font-semibold text-dark-100">系统设置</h1>
        <p className="text-sm text-dark-500 mt-1">配置LLM和Embedding服务</p>
      </div>

      {/* 统计卡片 */}
      <div className="px-6 py-4 grid grid-cols-4 gap-4">
        <StatCard
          icon={Server}
          label="LLM Provider"
          value={systemStats?.providers.llm || 0}
        />
        <StatCard
          icon={Database}
          label="Embedding Provider"
          value={systemStats?.providers.embedding || 0}
        />
        <StatCard
          icon={Zap}
          label="向量数据"
          value={systemStats?.vectorstore?.count || 0}
        />
        <StatCard
          icon={Database}
          label="已处理文档"
          value={systemStats?.documents.completed || 0}
        />
      </div>

      {/* 标签页 */}
      <div className="px-6 flex gap-1 border-b border-dark-800">
        <TabButton
          active={activeTab === 'llm'}
          onClick={() => setActiveTab('llm')}
        >
          LLM Provider
        </TabButton>
        <TabButton
          active={activeTab === 'embedding'}
          onClick={() => setActiveTab('embedding')}
        >
          Embedding Provider
        </TabButton>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'llm' ? (
          <LLMProviderList />
        ) : (
          <EmbeddingProviderList />
        )}
      </div>
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType
  label: string
  value: number
}) {
  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary-500/20 rounded-lg flex items-center justify-center">
          <Icon className="w-5 h-5 text-primary-400" />
        </div>
        <div>
          <p className="text-2xl font-semibold text-dark-100">{value}</p>
          <p className="text-sm text-dark-500">{label}</p>
        </div>
      </div>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
        active
          ? 'text-primary-400 border-primary-400'
          : 'text-dark-400 border-transparent hover:text-dark-200'
      )}
    >
      {children}
    </button>
  )
}

function LLMProviderList() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(
    null
  )
  const [formData, setFormData] = useState<LLMProviderCreate>({
    name: '',
    provider_type: 'openai',
    base_url: '',
    api_key: '',
    models: '',
    is_default: false,
    is_active: true,
  })
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
  } | null>(null)

  const { data: providers, isLoading } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => llmProviders.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: LLMProviderCreate) => llmProviders.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      closeModal()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LLMProviderCreate> }) =>
      llmProviders.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      closeModal()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => llmProviders.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: (id: number) => llmProviders.test(id),
    onSuccess: (result) => setTestResult(result),
    onError: (error: Error) =>
      setTestResult({ success: false, message: error.message }),
  })

  const openCreateModal = () => {
    setEditingProvider(null)
    setFormData({
      name: '',
      provider_type: 'openai',
      base_url: '',
      api_key: '',
      models: '["gpt-4o", "gpt-4o-mini"]',
      is_default: false,
      is_active: true,
    })
    setTestResult(null)
    setIsModalOpen(true)
  }

  const openEditModal = (provider: LLMProvider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      base_url: provider.base_url || '',
      api_key: '',
      models: provider.models || '',
      is_default: provider.is_default,
      is_active: provider.is_active,
    })
    setTestResult(null)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingProvider(null)
    setTestResult(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = { ...formData }
    if (editingProvider && !data.api_key) {
      delete (data as Record<string, unknown>).api_key
    }
    if (editingProvider) {
      updateMutation.mutate({ id: editingProvider.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <>
      <div className="flex justify-end mb-4">
        <Button onClick={openCreateModal}>
          <Plus className="w-4 h-4" />
          添加LLM Provider
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-3">
          {providers?.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              onEdit={() => openEditModal(provider)}
              onDelete={() => deleteMutation.mutate(provider.id)}
              onTest={() => testMutation.mutate(provider.id)}
              testing={testMutation.isPending}
            />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingProvider ? '编辑LLM Provider' : '添加LLM Provider'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="名称"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="如: OpenAI GPT-4"
            required
          />

          <Select
            label="类型"
            value={formData.provider_type}
            onChange={(e) =>
              setFormData({ ...formData, provider_type: e.target.value })
            }
            options={[
              { value: 'openai', label: 'OpenAI (兼容)' },
              { value: 'claude', label: 'Claude' },
              { value: 'ollama', label: 'Ollama' },
            ]}
          />

          <Input
            label="API地址"
            value={formData.base_url}
            onChange={(e) =>
              setFormData({ ...formData, base_url: e.target.value })
            }
            placeholder="如: https://api.openai.com/v1"
          />

          <Input
            label={editingProvider ? 'API密钥 (留空保持不变)' : 'API密钥'}
            type="password"
            value={formData.api_key}
            onChange={(e) =>
              setFormData({ ...formData, api_key: e.target.value })
            }
            placeholder="sk-..."
          />

          <Input
            label="可用模型 (JSON数组)"
            value={formData.models}
            onChange={(e) =>
              setFormData({ ...formData, models: e.target.value })
            }
            placeholder='["gpt-4o", "gpt-4o-mini"]'
          />

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={(e) =>
                  setFormData({ ...formData, is_default: e.target.checked })
                }
                className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500"
              />
              <span className="text-sm text-dark-300">设为默认</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500"
              />
              <span className="text-sm text-dark-300">启用</span>
            </label>
          </div>

          {testResult && (
            <div
              className={clsx(
                'p-3 rounded-lg text-sm',
                testResult.success
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              )}
            >
              {testResult.message}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={closeModal}>
              取消
            </Button>
            <Button
              type="submit"
              loading={createMutation.isPending || updateMutation.isPending}
            >
              {editingProvider ? '保存' : '添加'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  )
}

function EmbeddingProviderList() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProvider, setEditingProvider] =
    useState<EmbeddingProvider | null>(null)
  const [formData, setFormData] = useState<EmbeddingProviderCreate>({
    name: '',
    provider_type: 'siliconflow',
    base_url: '',
    api_key: '',
    model: '',
    dimensions: undefined,
    is_default: false,
    is_active: true,
  })
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
    dimensions?: number
  } | null>(null)

  const { data: providers, isLoading } = useQuery({
    queryKey: ['embedding-providers'],
    queryFn: () => embeddingProviders.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: EmbeddingProviderCreate) =>
      embeddingProviders.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-providers'] })
      closeModal()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number
      data: Partial<EmbeddingProviderCreate>
    }) => embeddingProviders.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-providers'] })
      closeModal()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => embeddingProviders.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['embedding-providers'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: (id: number) => embeddingProviders.test(id),
    onSuccess: (result) => setTestResult(result),
    onError: (error: Error) =>
      setTestResult({ success: false, message: error.message }),
  })

  const openCreateModal = () => {
    setEditingProvider(null)
    setFormData({
      name: '',
      provider_type: 'siliconflow',
      base_url: 'https://api.siliconflow.cn/v1/embeddings',
      api_key: '',
      model: 'Qwen/Qwen3-Embedding-8B',
      dimensions: undefined,
      is_default: false,
      is_active: true,
    })
    setTestResult(null)
    setIsModalOpen(true)
  }

  const openEditModal = (provider: EmbeddingProvider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      base_url: provider.base_url || '',
      api_key: '',
      model: provider.model,
      dimensions: provider.dimensions || undefined,
      is_default: provider.is_default,
      is_active: provider.is_active,
    })
    setTestResult(null)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingProvider(null)
    setTestResult(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data = { ...formData }
    if (editingProvider && !data.api_key) {
      delete (data as Record<string, unknown>).api_key
    }
    if (editingProvider) {
      updateMutation.mutate({ id: editingProvider.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  return (
    <>
      <div className="flex justify-end mb-4">
        <Button onClick={openCreateModal}>
          <Plus className="w-4 h-4" />
          添加Embedding Provider
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-3">
          {providers?.map((provider) => (
            <ProviderCard
              key={provider.id}
              provider={provider}
              onEdit={() => openEditModal(provider)}
              onDelete={() => deleteMutation.mutate(provider.id)}
              onTest={() => testMutation.mutate(provider.id)}
              testing={testMutation.isPending}
              showModel
            />
          ))}
        </div>
      )}

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={
          editingProvider ? '编辑Embedding Provider' : '添加Embedding Provider'
        }
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="名称"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="如: SiliconFlow Qwen3"
            required
          />

          <Select
            label="类型"
            value={formData.provider_type}
            onChange={(e) =>
              setFormData({ ...formData, provider_type: e.target.value })
            }
            options={[
              { value: 'siliconflow', label: 'SiliconFlow' },
              { value: 'openai', label: 'OpenAI (兼容)' },
              { value: 'ollama', label: 'Ollama' },
              { value: 'local', label: '本地模型' },
            ]}
          />

          <Input
            label="API地址"
            value={formData.base_url}
            onChange={(e) =>
              setFormData({ ...formData, base_url: e.target.value })
            }
            placeholder="如: https://api.siliconflow.cn/v1/embeddings"
          />

          <Input
            label={editingProvider ? 'API密钥 (留空保持不变)' : 'API密钥'}
            type="password"
            value={formData.api_key}
            onChange={(e) =>
              setFormData({ ...formData, api_key: e.target.value })
            }
            placeholder="sk-..."
            required={!editingProvider}
          />

          <Input
            label="模型"
            value={formData.model}
            onChange={(e) =>
              setFormData({ ...formData, model: e.target.value })
            }
            placeholder="Qwen/Qwen3-Embedding-8B"
            required
          />

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_default}
                onChange={(e) =>
                  setFormData({ ...formData, is_default: e.target.checked })
                }
                className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500"
              />
              <span className="text-sm text-dark-300">设为默认</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500"
              />
              <span className="text-sm text-dark-300">启用</span>
            </label>
          </div>

          {testResult && (
            <div
              className={clsx(
                'p-3 rounded-lg text-sm',
                testResult.success
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              )}
            >
              {testResult.message}
              {testResult.dimensions && (
                <span className="ml-2">• 向量维度: {testResult.dimensions}</span>
              )}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={closeModal}>
              取消
            </Button>
            <Button
              type="submit"
              loading={createMutation.isPending || updateMutation.isPending}
            >
              {editingProvider ? '保存' : '添加'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  )
}

function ProviderCard({
  provider,
  onEdit,
  onDelete,
  onTest,
  testing,
  showModel,
}: {
  provider: LLMProvider | EmbeddingProvider
  onEdit: () => void
  onDelete: () => void
  onTest: () => void
  testing: boolean
  showModel?: boolean
}) {
  return (
    <div className="bg-dark-900 border border-dark-800 rounded-xl p-4 flex items-center justify-between group hover:border-dark-700 transition-colors">
      <div className="flex items-center gap-4">
        <div
          className={clsx(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            provider.is_active ? 'bg-primary-500/20' : 'bg-dark-800'
          )}
        >
          <Server
            className={clsx(
              'w-5 h-5',
              provider.is_active ? 'text-primary-400' : 'text-dark-500'
            )}
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-dark-100">{provider.name}</h3>
            {provider.is_default && (
              <span className="px-1.5 py-0.5 bg-primary-500/20 text-primary-400 text-xs rounded">
                默认
              </span>
            )}
            {!provider.is_active && (
              <span className="px-1.5 py-0.5 bg-dark-700 text-dark-500 text-xs rounded">
                已禁用
              </span>
            )}
          </div>
          <div className="text-sm text-dark-500 mt-1">
            {provider.provider_type}
            {showModel &&
              'model' in provider &&
              provider.model &&
              ` • ${provider.model}`}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={onTest}
          disabled={testing}
        >
          {testing ? '测试中...' : '测试连接'}
        </Button>
        <Button variant="secondary" size="sm" onClick={onEdit}>
          <Edit className="w-4 h-4" />
        </Button>
        <Button variant="secondary" size="sm" onClick={onDelete}>
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
