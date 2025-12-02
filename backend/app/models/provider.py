"""
LLM 和 Embedding Provider 模型
"""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LLMProvider(Base):
    """LLM服务提供者配置"""
    __tablename__ = "llm_providers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="类型: openai/claude/ollama")
    base_url: Mapped[str | None] = mapped_column(String(500), comment="API地址")
    api_key: Mapped[str | None] = mapped_column(String(500), comment="API密钥(加密存储)")
    models: Mapped[str | None] = mapped_column(Text, comment="可用模型列表(JSON)")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmbeddingProvider(Base):
    """Embedding服务提供者配置"""
    __tablename__ = "embedding_providers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="显示名称")
    provider_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="类型: openai/ollama/local/huggingface",
    )
    base_url: Mapped[str | None] = mapped_column(String(500), comment="API地址")
    api_key: Mapped[str | None] = mapped_column(String(500), comment="API密钥(加密存储)")
    model: Mapped[str] = mapped_column(String(200), nullable=False, comment="模型名称")
    dimensions: Mapped[int | None] = mapped_column(Integer, comment="向量维度")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否默认")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
