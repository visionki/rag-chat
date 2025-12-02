"""
检索测试路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import get_db
from app.services.vectorstore_service import VectorStoreService
from app.services.embedding_service import EmbeddingService
from app.models import EmbeddingProvider
from app.logger import get_logger

logger = get_logger("rag-chat.search-test")
router = APIRouter(prefix="/api/search-test", tags=["search-test"])

vectorstore_service = VectorStoreService()
embedding_service = EmbeddingService()


class SearchTestRequest(BaseModel):
    """检索测试请求"""
    query: str = Field(..., description="查询关键词")
    top_k: int = Field(default=10, ge=1, le=50, description="返回结果数量")
    embedding_provider_id: Optional[int] = Field(None, description="嵌入模型提供商ID，不指定则使用默认")


class SearchResult(BaseModel):
    """检索结果"""
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float
    metadata: dict


class SearchTestResponse(BaseModel):
    """检索测试响应"""
    query: str
    top_k: int
    embedding_provider: str
    results: List[SearchResult]
    total_time_ms: int


@router.post("", response_model=SearchTestResponse)
async def test_search(
    request: SearchTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    测试检索功能
    
    - **query**: 查询关键词
    - **top_k**: 返回结果数量（默认10）
    - **embedding_provider_id**: 嵌入模型提供商ID（可选）
    """
    import time
    
    start_time = time.time()
    
    # 获取嵌入模型提供商
    if request.embedding_provider_id:
        result = await db.execute(
            select(EmbeddingProvider).where(EmbeddingProvider.id == request.embedding_provider_id)
        )
        embedding_provider = result.scalar_one_or_none()
        if not embedding_provider:
            raise HTTPException(status_code=404, detail="嵌入模型提供商不存在")
    else:
        # 使用默认嵌入模型
        result = await db.execute(
            select(EmbeddingProvider).where(EmbeddingProvider.is_default == True)
        )
        embedding_provider = result.scalar_one_or_none()
        if not embedding_provider:
            raise HTTPException(status_code=400, detail="未找到默认嵌入模型，请先配置")
    
    logger.info(f"🔍 开始检索测试: query='{request.query}', top_k={request.top_k}, provider={embedding_provider.name}")
    
    # 执行检索
    try:
        docs_with_scores = await vectorstore_service.similarity_search_with_score(
            embedding_provider=embedding_provider,
            query=request.query,
            k=request.top_k
        )
        
        # 构建结果
        results = []
        for doc, score in docs_with_scores:
            results.append(SearchResult(
                document_id=str(doc.metadata.get("document_id", "")),
                filename=str(doc.metadata.get("filename", "")),
                chunk_index=int(doc.metadata.get("chunk_index", 0)),
                content=doc.page_content,
                score=float(score),
                metadata=doc.metadata
            ))
        
        total_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ 检索完成: 找到 {len(results)} 个结果 ({total_time_ms}ms)")
        
        return SearchTestResponse(
            query=request.query,
            top_k=request.top_k,
            embedding_provider=embedding_provider.name,
            results=results,
            total_time_ms=total_time_ms
        )
        
    except Exception as e:
        logger.error(f"❌ 检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/providers")
async def get_embedding_providers(db: AsyncSession = Depends(get_db)):
    """获取所有可用的嵌入模型提供商"""
    result = await db.execute(
        select(EmbeddingProvider).where(EmbeddingProvider.is_active == True)
    )
    providers = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "model": p.model,
            "is_default": p.is_default
        }
        for p in providers
    ]

