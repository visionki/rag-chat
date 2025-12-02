import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, Plus, Trash2, Edit, MessageSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { chatbots, llmProviders } from '../../api'
import type { Chatbot, ChatbotCreate } from '../../api'
import Button from '../../components/Button'
import Modal from '../../components/Modal'
import Input from '../../components/Input'
import Select from '../../components/Select'
import EmptyState from '../../components/EmptyState'

export default function ChatbotsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingBot, setEditingBot] = useState<Chatbot | null>(null)
  const [formData, setFormData] = useState<ChatbotCreate>({
    name: '',
    description: '',
    system_prompt: '',
    llm_provider_id: undefined,
    model: '',
    temperature: 0.7,
    max_tokens: 2048,
    use_knowledge_base: true,
    top_k: 5,
    use_query_rewrite: false,
    rewrite_provider_id: undefined,
    rewrite_model: '',
  })

  // 获取Chatbot列表
  const { data: chatbotList, isLoading } = useQuery({
    queryKey: ['chatbots'],
    queryFn: () => chatbots.list(),
  })

  // 获取LLM Provider列表
  const { data: providers } = useQuery({
    queryKey: ['llm-providers'],
    queryFn: () => llmProviders.list(),
  })

  // 创建Chatbot
  const createMutation = useMutation({
    mutationFn: (data: ChatbotCreate) => chatbots.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      closeModal()
    },
  })

  // 更新Chatbot
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ChatbotCreate> }) =>
      chatbots.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
      closeModal()
    },
  })

  // 删除Chatbot
  const deleteMutation = useMutation({
    mutationFn: (id: number) => chatbots.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] })
    },
  })

  const openCreateModal = () => {
    setEditingBot(null)
    setFormData({
      name: '',
      description: '',
      system_prompt: '你是一个有用的AI助手，请基于提供的知识库内容回答用户的问题。',
      llm_provider_id: providers?.[0]?.id,
      model: '',
      temperature: 0.7,
      max_tokens: 2048,
      use_knowledge_base: true,
      top_k: 5,
      use_query_rewrite: false,
      rewrite_provider_id: undefined,
      rewrite_model: '',
    })
    setIsModalOpen(true)
  }

  const openEditModal = (bot: Chatbot) => {
    setEditingBot(bot)
    setFormData({
      name: bot.name,
      description: bot.description || '',
      system_prompt: bot.system_prompt || '',
      llm_provider_id: bot.llm_provider_id || undefined,
      model: bot.model || '',
      temperature: bot.temperature,
      max_tokens: bot.max_tokens,
      use_knowledge_base: bot.use_knowledge_base,
      top_k: bot.top_k,
      use_query_rewrite: bot.use_query_rewrite,
      rewrite_provider_id: bot.rewrite_provider_id || undefined,
      rewrite_model: bot.rewrite_model || '',
    })
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingBot(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingBot) {
      updateMutation.mutate({ id: editingBot.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  // 获取选中Provider的模型列表
  const selectedProvider = providers?.find(
    (p) => p.id === formData.llm_provider_id
  )
  const modelOptions = selectedProvider?.models
    ? JSON.parse(selectedProvider.models).map((m: string) => ({
        value: m,
        label: m,
      }))
    : []

  // 获取重写Provider的模型列表
  const rewriteProvider = providers?.find(
    (p) => p.id === formData.rewrite_provider_id
  )
  const rewriteModelOptions = rewriteProvider?.models
    ? JSON.parse(rewriteProvider.models).map((m: string) => ({
        value: m,
        label: m,
      }))
    : []

  return (
    <div className="h-full flex flex-col">
      {/* 顶部栏 */}
      <div className="px-6 py-4 border-b border-dark-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-dark-100">机器人管理</h1>
          <p className="text-sm text-dark-500 mt-1">创建和管理你的AI助手</p>
        </div>
        <Button onClick={openCreateModal}>
          <Plus className="w-4 h-4" />
          创建机器人
        </Button>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
          </div>
        ) : chatbotList?.items.length === 0 ? (
          <EmptyState
            icon={Bot}
            title="还没有机器人"
            description="创建你的第一个AI机器人，开始智能问答"
            action={
              <Button onClick={openCreateModal}>
                <Plus className="w-4 h-4" />
                创建机器人
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {chatbotList?.items.map((bot) => (
              <div
                key={bot.id}
                className="bg-dark-900 border border-dark-800 rounded-xl p-5 hover:border-dark-700 transition-colors group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 bg-primary-500/20 rounded-xl flex items-center justify-center">
                    <Bot className="w-5 h-5 text-primary-400" />
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      className="p-1.5 text-dark-400 hover:text-dark-200 hover:bg-dark-800 rounded-lg"
                      onClick={() => openEditModal(bot)}
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-800 rounded-lg"
                      onClick={() => deleteMutation.mutate(bot.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <h3 className="font-medium text-dark-100 mb-1">{bot.name}</h3>
                {bot.description && (
                  <p className="text-sm text-dark-500 mb-3 line-clamp-2">
                    {bot.description}
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-dark-500">
                  <div className="flex items-center gap-1">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>{bot.conversation_count} 会话</span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => navigate(`/chat/${bot.id}`)}
                  >
                    开始对话
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 创建/编辑模态框 */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingBot ? '编辑机器人' : '创建机器人'}
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="名称"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="给机器人取个名字"
            required
          />

          <Input
            label="描述"
            value={formData.description}
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
            placeholder="简单描述这个机器人的用途"
          />

          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-dark-300">
              系统提示词
            </label>
            <textarea
              value={formData.system_prompt}
              onChange={(e) =>
                setFormData({ ...formData, system_prompt: e.target.value })
              }
              placeholder="定义机器人的角色和行为..."
              rows={4}
              className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-lg text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-primary-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Select
              label="LLM Provider"
              value={formData.llm_provider_id || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  llm_provider_id: Number(e.target.value) || undefined,
                  model: '',
                })
              }
              options={[
                { value: '', label: '选择Provider' },
                ...(providers?.map((p) => ({ value: p.id, label: p.name })) ||
                  []),
              ]}
            />

            <Select
              label="模型"
              value={formData.model || ''}
              onChange={(e) =>
                setFormData({ ...formData, model: e.target.value })
              }
              options={[
                { value: '', label: '选择模型' },
                ...modelOptions,
              ]}
              disabled={!formData.llm_provider_id}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-dark-300">
                温度: {formData.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    temperature: parseFloat(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>

            <Input
              label="最大Token"
              type="number"
              value={formData.max_tokens}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  max_tokens: parseInt(e.target.value) || 2048,
                })
              }
              min={1}
              max={128000}
            />
          </div>

          <div className="flex flex-col gap-3">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.use_knowledge_base}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    use_knowledge_base: e.target.checked,
                  })
                }
                className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500 focus:ring-primary-500"
              />
              <span className="text-sm text-dark-300">使用知识库</span>
            </label>

            {formData.use_knowledge_base && (
              <div className="space-y-3 pl-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-dark-500">检索数量:</span>
                  <input
                    type="number"
                    value={formData.top_k}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        top_k: parseInt(e.target.value) || 5,
                      })
                    }
                    min={1}
                    max={20}
                    className="w-16 px-2 py-1 bg-dark-900 border border-dark-700 rounded text-dark-100 text-sm"
                  />
                </div>

                {/* 查询重写配置 */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.use_query_rewrite}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        use_query_rewrite: e.target.checked,
                      })
                    }
                    className="w-4 h-4 rounded border-dark-700 bg-dark-900 text-primary-500 focus:ring-primary-500"
                  />
                  <span className="text-sm text-dark-300">启用查询重写</span>
                  <span className="text-xs text-dark-500">(解决指代消解问题)</span>
                </label>

                {formData.use_query_rewrite && (
                  <div className="grid grid-cols-2 gap-3 pl-6 pt-1">
                    <Select
                      label="重写 Provider"
                      value={formData.rewrite_provider_id || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rewrite_provider_id: Number(e.target.value) || undefined,
                          rewrite_model: '',
                        })
                      }
                      options={[
                        { value: '', label: '选择Provider' },
                        ...(providers?.map((p) => ({ value: p.id, label: p.name })) || []),
                      ]}
                    />
                    <Select
                      label="重写模型"
                      value={formData.rewrite_model || ''}
                      onChange={(e) =>
                        setFormData({ ...formData, rewrite_model: e.target.value })
                      }
                      options={[
                        { value: '', label: '选择模型' },
                        ...rewriteModelOptions,
                      ]}
                      disabled={!formData.rewrite_provider_id}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={closeModal}>
              取消
            </Button>
            <Button
              type="submit"
              loading={createMutation.isPending || updateMutation.isPending}
            >
              {editingBot ? '保存' : '创建'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

