"""
会话和消息相关的Pydantic Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ============ Message ============

class MessageBase(BaseModel):
    """消息基础Schema"""
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class MessageCreate(MessageBase):
    """创建消息"""
    pass


class MessageResponse(MessageBase):
    """消息响应"""
    id: int
    conversation_id: int
    tokens_used: int | None
    sources: str | None = Field(None, description="引用来源(JSON)")
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ Conversation ============

class ConversationBase(BaseModel):
    """会话基础Schema"""
    title: str | None = Field(None, description="会话标题")


class ConversationCreate(ConversationBase):
    """创建会话"""
    pass


class ConversationResponse(ConversationBase):
    """会话响应"""
    id: int
    chatbot_id: int
    created_at: datetime
    updated_at: datetime
    message_count: int = Field(0, description="消息数量")
    last_message: str | None = Field(None, description="最后一条消息预览")
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """会话详情响应(包含消息)"""
    messages: list[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """会话列表响应"""
    total: int
    items: list[ConversationResponse]


# ============ Chat ============

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, description="用户消息")
    stream: bool = Field(True, description="是否流式响应")


class ChatResponse(BaseModel):
    """聊天响应(非流式)"""
    message: MessageResponse
    sources: list[dict] | None = Field(None, description="引用的文档来源")


class SourceDocument(BaseModel):
    """来源文档"""
    document_id: int
    filename: str
    content: str
    score: float


