"""
FastAPI应用主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
from app.config import settings
from app.database import init_db, close_db
from app.logger import setup_logging, get_logger
from app.routers import (
    providers_router,
    documents_router,
    chatbots_router,
    conversations_router,
    chat_logs_router,
    search_test_router
)

# 初始化日志
setup_logging()
logger = get_logger("rag-chat.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")
    logger.info(f"📁 数据库: {settings.DATABASE_URL}")
    logger.info(f"📂 上传目录: {settings.UPLOAD_DIR}")
    logger.info(f"📂 向量库目录: {settings.CHROMA_DIR}")
    logger.info(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")
    
    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库初始化完成")
    
    logger.info(f"🌐 API文档: http://localhost:8000/docs")
    logger.info("=" * 50)
    logger.info("✨ 服务启动成功，等待请求...")
    
    yield
    
    # 关闭时清理资源
    logger.info("🛑 服务正在关闭...")
    await close_db()
    logger.info("👋 服务已停止")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="文档问答系统API",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    # 跳过健康检查和静态资源的日志
    skip_paths = ["/api/health", "/docs", "/openapi.json", "/favicon.ico"]
    should_log = not any(request.url.path.startswith(p) for p in skip_paths)
    
    if should_log:
        logger.info(f"➡️  {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    if should_log:
        duration = (time.time() - start_time) * 1000
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(f"{status_emoji} {request.method} {request.url.path} - {response.status_code} ({duration:.1f}ms)")
    
    return response


# 注册路由
app.include_router(providers_router)
app.include_router(documents_router)
app.include_router(chatbots_router)
app.include_router(conversations_router)
app.include_router(chat_logs_router)
app.include_router(search_test_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    from sqlalchemy import select, func
    from app.database import async_session_maker
    from app.models import Document, Chatbot, Conversation, LLMProvider, EmbeddingProvider
    from app.services.vectorstore_service import VectorStoreService
    
    logger.debug("📊 获取系统统计信息")
    
    async with async_session_maker() as db:
        # 文档统计
        doc_count = await db.execute(select(func.count(Document.id)))
        doc_completed = await db.execute(
            select(func.count(Document.id)).where(Document.status == "completed")
        )
        
        # Chatbot统计
        chatbot_count = await db.execute(select(func.count(Chatbot.id)))
        
        # 会话统计
        conv_count = await db.execute(select(func.count(Conversation.id)))
        
        # Provider统计
        llm_count = await db.execute(select(func.count(LLMProvider.id)))
        embedding_count = await db.execute(select(func.count(EmbeddingProvider.id)))
        
        # 向量存储统计
        vs_service = VectorStoreService()
        vs_stats = vs_service.get_collection_stats()
        
        return {
            "documents": {
                "total": doc_count.scalar(),
                "completed": doc_completed.scalar()
            },
            "chatbots": chatbot_count.scalar(),
            "conversations": conv_count.scalar(),
            "providers": {
                "llm": llm_count.scalar(),
                "embedding": embedding_count.scalar()
            },
            "vectorstore": vs_stats
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
