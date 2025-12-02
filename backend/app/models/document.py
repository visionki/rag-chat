"""
文档模型
"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False, comment="原始文件名")
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, comment="存储路径")
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="文件类型")
    file_size: Mapped[int | None] = mapped_column(Integer, comment="文件大小(字节)")
    content_hash: Mapped[str | None] = mapped_column(String(64), comment="内容哈希(去重)")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, comment="分块数量")
    status: Mapped[str] = mapped_column(String(50), default="pending", comment="状态: pending/processing/completed/failed")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    
    # 关联使用的Embedding Provider
    embedding_provider_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey("embedding_providers.id", ondelete="SET NULL"),
        comment="使用的Embedding Provider"
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    embedding_provider = relationship("EmbeddingProvider", lazy="selectin")


