"""
文档管理API路由
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Document
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.logger import get_logger

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger("rag-chat.api.documents")

document_service = DocumentService()


async def _process_document_async(document_id: int):
    """异步处理文档"""
    from app.database import async_session_maker
    
    logger.info(f"📋 后台任务开始: 处理文档 ID={document_id}")
    
    async with async_session_maker() as db:
        try:
            await document_service.process_document(db, document_id)
            await db.commit()
            logger.info(f"✅ 后台任务完成: 文档 ID={document_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 后台任务异常: {e}", exc_info=True)
            # 更新文档状态
            try:
                async with async_session_maker() as db2:
                    result = await db2.execute(
                        select(Document).where(Document.id == document_id)
                    )
                    document = result.scalar_one_or_none()
                    if document:
                        document.status = "failed"
                        document.error_message = str(e)
                    await db2.commit()
            except Exception as e2:
                logger.error(f"❌ 更新文档状态失败: {e2}")


def process_document_task(document_id: int):
    """后台任务：处理文档（同步包装）"""
    logger.info(f"🚀 启动后台任务: 文档 ID={document_id}")
    try:
        # 创建新的事件循环来运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_process_document_async(document_id))
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"❌ 后台任务执行失败: {e}", exc_info=True)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """上传文档"""
    logger.info(f"📤 收到文档上传请求: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        content = await file.read()
        result = await document_service.upload_document(db, file.filename, content)
        
        # ⚠️ 关键：手动提交事务，确保数据写入数据库后再启动后台任务
        # 否则后台任务的新连接可能看不到未提交的数据
        await db.commit()
        logger.info(f"💾 文档事务已提交: ID={result.id}")
        
        logger.info(f"📝 文档已保存，添加后台处理任务: 文档ID={result.id}")
        
        # 添加后台处理任务
        background_tasks.add_task(process_document_task, result.id)
        
        return result
    except ValueError as e:
        logger.error(f"❌ 上传失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取文档列表"""
    return await document_service.list_documents(db, skip, limit, status)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取文档详情"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除文档"""
    success = await document_service.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """重新处理文档"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 更新状态为pending
    document.status = "pending"
    document.error_message = None
    
    # ⚠️ 关键：手动提交事务，确保状态更新后再启动后台任务
    await db.commit()
    await db.refresh(document)
    
    logger.info(f"🔄 重新处理文档: {document.filename}")
    
    # 添加后台处理任务
    background_tasks.add_task(process_document_task, document_id)
    
    return DocumentResponse.model_validate(document)


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document_now(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """立即处理文档（同步，不使用后台任务）"""
    document = await document_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    logger.info(f"⚡ 立即处理文档: {document.filename}")
    
    try:
        result = await document_service.process_document(db, document_id)
        return DocumentResponse.model_validate(result)
    except Exception as e:
        logger.error(f"❌ 处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
