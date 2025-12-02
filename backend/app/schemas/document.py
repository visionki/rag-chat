"""
文档相关的Pydantic Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """文档基础Schema"""
    filename: str = Field(..., description="文件名")


class DocumentCreate(DocumentBase):
    """创建文档(内部使用)"""
    file_path: str
    file_type: str
    file_size: int | None = None
    content_hash: str | None = None


class DocumentUpdate(BaseModel):
    """更新文档"""
    filename: str | None = None


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    filename: str
    file_type: str
    file_size: int | None
    chunk_count: int
    status: str
    error_message: str | None
    embedding_provider_id: int | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    items: list[DocumentResponse]


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    id: int
    filename: str
    status: str
    message: str


