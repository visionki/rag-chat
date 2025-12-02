"""
Chatbot模型
"""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Chatbot(Base):
    """Chatbot配置模型"""
    __tablename__ = "chatbots"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="Bot名称")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")
    system_prompt: Mapped[str | None] = mapped_column(Text, comment="系统提示词")
    
    # LLM配置
    llm_provider_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="SET NULL"),
        comment="使用的LLM Provider"
    )
    model: Mapped[str | None] = mapped_column(String(100), comment="使用的模型")
    temperature: Mapped[float] = mapped_column(Float, default=0.7, comment="温度")
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, comment="最大token")
    
    # 知识库配置
    use_knowledge_base: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否使用知识库")
    top_k: Mapped[int] = mapped_column(Integer, default=5, comment="检索文档数量")
    
    # 查询重写配置
    use_query_rewrite: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否使用查询重写")
    rewrite_provider_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="SET NULL"),
        comment="查询重写使用的LLM Provider"
    )
    rewrite_model: Mapped[str | None] = mapped_column(String(100), comment="查询重写使用的模型")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    llm_provider = relationship("LLMProvider", foreign_keys=[llm_provider_id], lazy="selectin")
    rewrite_provider = relationship("LLMProvider", foreign_keys=[rewrite_provider_id], lazy="selectin")
    conversations = relationship("Conversation", back_populates="chatbot", cascade="all, delete-orphan")
