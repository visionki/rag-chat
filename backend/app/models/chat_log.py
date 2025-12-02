"""
聊天日志模型
"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ChatLog(Base):
    """聊天日志模型 - 记录每次问答的详细信息"""
    __tablename__ = "chat_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 关联信息
    conversation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="SET NULL"),
        comment="所属会话"
    )
    chatbot_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("chatbots.id", ondelete="SET NULL"),
        comment="所属Bot"
    )
    message_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="SET NULL"),
        comment="关联的助手消息ID"
    )
    
    # Provider信息
    llm_provider_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="SET NULL"),
        comment="LLM Provider"
    )
    llm_provider_name: Mapped[str | None] = mapped_column(String(100), comment="Provider名称")
    model: Mapped[str | None] = mapped_column(String(100), comment="使用的模型")
    
    # 输入输出
    input_text: Mapped[str] = mapped_column(Text, nullable=False, comment="用户输入")
    output_text: Mapped[str | None] = mapped_column(Text, comment="模型输出")
    system_prompt: Mapped[str | None] = mapped_column(Text, comment="系统提示词")
    
    # 查询重写相关
    use_query_rewrite: Mapped[bool] = mapped_column(default=False, comment="是否使用查询重写")
    rewrite_time_ms: Mapped[int | None] = mapped_column(Integer, comment="查询重写耗时(毫秒)")
    rewritten_query: Mapped[str | None] = mapped_column(Text, comment="重写后的查询")
    
    # RAG相关
    use_rag: Mapped[bool] = mapped_column(default=False, comment="是否使用RAG")
    rag_query_time_ms: Mapped[int | None] = mapped_column(Integer, comment="RAG检索耗时(毫秒)")
    rag_results_count: Mapped[int | None] = mapped_column(Integer, comment="RAG检索结果数量")
    rag_results: Mapped[str | None] = mapped_column(Text, comment="RAG检索结果(JSON)")
    
    # 性能指标
    total_time_ms: Mapped[int | None] = mapped_column(Integer, comment="总响应时间(毫秒)")
    llm_time_ms: Mapped[int | None] = mapped_column(Integer, comment="LLM响应时间(毫秒)")
    input_tokens: Mapped[int | None] = mapped_column(Integer, comment="输入token数")
    output_tokens: Mapped[int | None] = mapped_column(Integer, comment="输出token数")
    
    # 状态
    status: Mapped[str] = mapped_column(String(20), default="success", comment="状态: success/error")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 关系
    conversation = relationship("Conversation", lazy="selectin")
    chatbot = relationship("Chatbot", lazy="selectin")
    llm_provider = relationship("LLMProvider", lazy="selectin")
    message = relationship("Message", lazy="selectin")


