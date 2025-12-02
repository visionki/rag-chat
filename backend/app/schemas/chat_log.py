"""
聊天日志相关的Pydantic Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class ChatLogResponse(BaseModel):
    """聊天日志响应"""
    id: int
    conversation_id: int | None
    chatbot_id: int | None
    message_id: int | None
    
    # Provider信息
    llm_provider_id: int | None
    llm_provider_name: str | None
    model: str | None
    
    # 输入输出
    input_text: str
    output_text: str | None
    
    # 查询重写相关
    use_query_rewrite: bool = False
    rewrite_time_ms: int | None = None
    rewritten_query: str | None = None
    
    # RAG相关
    use_rag: bool
    rag_query_time_ms: int | None
    rag_results_count: int | None
    rag_results: str | None
    
    # 性能指标
    total_time_ms: int | None
    llm_time_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    
    # 状态
    status: str
    error_message: str | None
    
    created_at: datetime
    
    # 关联名称（用于展示）
    chatbot_name: str | None = None
    conversation_title: str | None = None
    
    class Config:
        from_attributes = True


class ChatLogListResponse(BaseModel):
    """聊天日志列表响应"""
    total: int
    items: list[ChatLogResponse]


class ChatLogFilter(BaseModel):
    """日志筛选条件"""
    chatbot_id: int | None = None
    conversation_id: int | None = None
    message_id: int | None = None
    llm_provider_id: int | None = None
    model: str | None = None
    status: str | None = None
    use_rag: bool | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ChatLogStats(BaseModel):
    """日志统计"""
    total_requests: int
    success_count: int
    error_count: int
    avg_total_time_ms: float | None
    avg_rag_time_ms: float | None
    avg_llm_time_ms: float | None
    total_input_tokens: int
    total_output_tokens: int


