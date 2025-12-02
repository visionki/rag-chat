"""
Chatbot相关的Pydantic Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ChatbotBase(BaseModel):
    """Chatbot基础Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="Bot名称")
    description: str | None = Field(None, description="描述")
    system_prompt: str | None = Field(None, description="系统提示词")
    llm_provider_id: int | None = Field(None, description="LLM Provider ID")
    model: str | None = Field(None, description="模型名称")
    temperature: float = Field(0.7, ge=0, le=2, description="温度")
    max_tokens: int = Field(2048, ge=1, le=128000, description="最大token")
    use_knowledge_base: bool = Field(True, description="是否使用知识库")
    top_k: int = Field(5, ge=1, le=20, description="检索文档数量")
    # 查询重写配置
    use_query_rewrite: bool = Field(False, description="是否使用查询重写")
    rewrite_provider_id: int | None = Field(None, description="查询重写 LLM Provider ID")
    rewrite_model: str | None = Field(None, description="查询重写模型名称")


class ChatbotCreate(ChatbotBase):
    """创建Chatbot"""
    pass


class ChatbotUpdate(BaseModel):
    """更新Chatbot"""
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    system_prompt: str | None = None
    llm_provider_id: int | None = None
    model: str | None = None
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, ge=1, le=128000)
    use_knowledge_base: bool | None = None
    top_k: int | None = Field(None, ge=1, le=20)
    use_query_rewrite: bool | None = None
    rewrite_provider_id: int | None = None
    rewrite_model: str | None = None


class ChatbotResponse(ChatbotBase):
    """Chatbot响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    conversation_count: int = Field(0, description="会话数量")
    
    class Config:
        from_attributes = True


class ChatbotListResponse(BaseModel):
    """Chatbot列表响应"""
    total: int
    items: list[ChatbotResponse]
