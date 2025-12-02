"""
会话和消息模型
"""
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Conversation(Base):
    """会话模型"""
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chatbot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chatbots.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属Bot"
    )
    title: Mapped[str | None] = mapped_column(String(500), comment="会话标题")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    chatbot = relationship("Chatbot", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属会话"
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False, comment="角色: user/assistant/system")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    tokens_used: Mapped[int | None] = mapped_column(Integer, comment="使用的token数")
    sources: Mapped[str | None] = mapped_column(Text, comment="引用的文档来源(JSON)")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


