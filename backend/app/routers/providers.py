"""
Provider管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models import LLMProvider, EmbeddingProvider
from app.schemas.provider import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    EmbeddingProviderCreate,
    EmbeddingProviderUpdate,
    EmbeddingProviderResponse,
    ProviderTestResponse,
)
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.logger import get_logger

router = APIRouter(prefix="/api", tags=["providers"])
logger = get_logger("rag-chat.api.providers")


# ============ LLM Provider ============

@router.post("/llm-providers", response_model=LLMProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_llm_provider(
    data: LLMProviderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建LLM Provider"""
    logger.info(f"➕ 创建LLM Provider: {data.name} ({data.provider_type})")
    
    # 如果设为默认，先取消其他默认
    if data.is_default:
        await db.execute(
            update(LLMProvider).values(is_default=False)
        )
    
    provider = LLMProvider(**data.model_dump())
    db.add(provider)
    await db.flush()
    await db.refresh(provider)
    
    logger.info(f"✅ LLM Provider已创建: ID={provider.id}")
    return LLMProviderResponse.from_orm_with_mask(provider)


@router.get("/llm-providers", response_model=list[LLMProviderResponse])
async def list_llm_providers(
    db: AsyncSession = Depends(get_db)
):
    """获取LLM Provider列表"""
    result = await db.execute(
        select(LLMProvider).order_by(LLMProvider.is_default.desc(), LLMProvider.created_at.desc())
    )
    providers = result.scalars().all()
    return [LLMProviderResponse.from_orm_with_mask(p) for p in providers]


@router.get("/llm-providers/{provider_id}", response_model=LLMProviderResponse)
async def get_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取LLM Provider详情"""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    return LLMProviderResponse.from_orm_with_mask(provider)


@router.put("/llm-providers/{provider_id}", response_model=LLMProviderResponse)
async def update_llm_provider(
    provider_id: int,
    data: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新LLM Provider"""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果设为默认，先取消其他默认
    if update_data.get("is_default"):
        await db.execute(
            update(LLMProvider).where(LLMProvider.id != provider_id).values(is_default=False)
        )
    
    for key, value in update_data.items():
        setattr(provider, key, value)
    
    await db.flush()
    await db.refresh(provider)
    
    logger.info(f"✏️  LLM Provider已更新: {provider.name}")
    return LLMProviderResponse.from_orm_with_mask(provider)


@router.delete("/llm-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除LLM Provider"""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    
    logger.info(f"🗑️  删除LLM Provider: {provider.name}")
    await db.delete(provider)


@router.post("/llm-providers/{provider_id}/test", response_model=ProviderTestResponse)
async def test_llm_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试LLM Provider连接"""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="LLM Provider not found")
    
    llm_service = LLMService()
    return await llm_service.test_provider(provider)



# ============ Embedding Provider ============

@router.post("/embedding-providers", response_model=EmbeddingProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_embedding_provider(
    data: EmbeddingProviderCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建Embedding Provider"""
    logger.info(f"➕ 创建Embedding Provider: {data.name} ({data.provider_type})")
    
    # 如果设为默认，先取消其他默认
    if data.is_default:
        await db.execute(
            update(EmbeddingProvider).values(is_default=False)
        )
    
    provider = EmbeddingProvider(**data.model_dump())
    db.add(provider)
    await db.flush()
    await db.refresh(provider)
    
    logger.info(f"✅ Embedding Provider已创建: ID={provider.id}")
    return EmbeddingProviderResponse.from_orm_with_mask(provider)


@router.get("/embedding-providers", response_model=list[EmbeddingProviderResponse])
async def list_embedding_providers(
    db: AsyncSession = Depends(get_db)
):
    """获取Embedding Provider列表"""
    result = await db.execute(
        select(EmbeddingProvider).order_by(EmbeddingProvider.is_default.desc(), EmbeddingProvider.created_at.desc())
    )
    providers = result.scalars().all()
    return [EmbeddingProviderResponse.from_orm_with_mask(p) for p in providers]


@router.get("/embedding-providers/{provider_id}", response_model=EmbeddingProviderResponse)
async def get_embedding_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取Embedding Provider详情"""
    result = await db.execute(
        select(EmbeddingProvider).where(EmbeddingProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Embedding Provider not found")
    return EmbeddingProviderResponse.from_orm_with_mask(provider)


@router.put("/embedding-providers/{provider_id}", response_model=EmbeddingProviderResponse)
async def update_embedding_provider(
    provider_id: int,
    data: EmbeddingProviderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新Embedding Provider"""
    result = await db.execute(
        select(EmbeddingProvider).where(EmbeddingProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Embedding Provider not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 如果设为默认，先取消其他默认
    if update_data.get("is_default"):
        await db.execute(
            update(EmbeddingProvider).where(EmbeddingProvider.id != provider_id).values(is_default=False)
        )
    
    for key, value in update_data.items():
        setattr(provider, key, value)
    
    await db.flush()
    await db.refresh(provider)
    
    logger.info(f"✏️  Embedding Provider已更新: {provider.name}")
    return EmbeddingProviderResponse.from_orm_with_mask(provider)


@router.delete("/embedding-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embedding_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除Embedding Provider"""
    result = await db.execute(
        select(EmbeddingProvider).where(EmbeddingProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Embedding Provider not found")
    
    logger.info(f"🗑️  删除Embedding Provider: {provider.name}")
    await db.delete(provider)


@router.post("/embedding-providers/{provider_id}/test", response_model=ProviderTestResponse)
async def test_embedding_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):
    """测试Embedding Provider连接"""
    result = await db.execute(
        select(EmbeddingProvider).where(EmbeddingProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Embedding Provider not found")
    
    embedding_service = EmbeddingService()
    test_result = await embedding_service.test_provider(provider)
    
    return ProviderTestResponse(
        success=test_result["success"],
        message=test_result["message"],
        dimensions=test_result.get("dimensions")
    )
