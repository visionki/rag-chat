"""
Provider相关的Pydantic Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


# ============ LLM Provider ============

class LLMProviderBase(BaseModel):
    """LLM Provider基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    provider_type: str = Field(..., description="类型: openai/claude/ollama")
    base_url: str | None = Field(None, description="API地址")
    api_key: str | None = Field(None, description="API密钥")
    models: str | None = Field(None, description="可用模型列表(JSON数组)")
    is_default: bool = Field(False, description="是否默认")
    is_active: bool = Field(True, description="是否启用")


class LLMProviderCreate(LLMProviderBase):
    """创建LLM Provider"""
    pass


class LLMProviderUpdate(BaseModel):
    """更新LLM Provider"""
    name: str | None = Field(None, min_length=1, max_length=100)
    provider_type: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    models: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class LLMProviderResponse(LLMProviderBase):
    """LLM Provider响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 隐藏API密钥
    api_key: str | None = Field(None, exclude=True)
    has_api_key: bool = Field(False, description="是否配置了API密钥")
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_mask(cls, obj):
        """从ORM对象创建，并处理密钥掩码"""
        data = {
            "id": obj.id,
            "name": obj.name,
            "provider_type": obj.provider_type,
            "base_url": obj.base_url,
            "models": obj.models,
            "is_default": obj.is_default,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "has_api_key": bool(obj.api_key),
        }
        return cls(**data)


# ============ Embedding Provider ============

class EmbeddingProviderBase(BaseModel):
    """Embedding Provider基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    provider_type: str = Field(..., description="类型: openai/ollama/local/huggingface")
    base_url: str | None = Field(None, description="API地址")
    api_key: str | None = Field(None, description="API密钥")
    model: str = Field(..., description="模型名称")
    dimensions: int | None = Field(None, description="向量维度")
    is_default: bool = Field(False, description="是否默认")
    is_active: bool = Field(True, description="是否启用")


class EmbeddingProviderCreate(EmbeddingProviderBase):
    """创建Embedding Provider"""
    pass


class EmbeddingProviderUpdate(BaseModel):
    """更新Embedding Provider"""
    name: str | None = Field(None, min_length=1, max_length=100)
    provider_type: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    dimensions: int | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class EmbeddingProviderResponse(EmbeddingProviderBase):
    """Embedding Provider响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 隐藏API密钥
    api_key: str | None = Field(None, exclude=True)
    has_api_key: bool = Field(False, description="是否配置了API密钥")
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_mask(cls, obj):
        """从ORM对象创建，并处理密钥掩码"""
        data = {
            "id": obj.id,
            "name": obj.name,
            "provider_type": obj.provider_type,
            "base_url": obj.base_url,
            "model": obj.model,
            "dimensions": obj.dimensions,
            "is_default": obj.is_default,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "has_api_key": bool(obj.api_key),
        }
        return cls(**data)


class ProviderTestRequest(BaseModel):
    """测试Provider连接请求"""
    pass


class ProviderTestResponse(BaseModel):
    """测试Provider连接响应"""
    success: bool
    message: str
    models: list[str] | None = None
    dimensions: int | None = None
