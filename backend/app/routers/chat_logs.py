"""
聊天日志API路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.chat_log import ChatLogResponse, ChatLogListResponse, ChatLogFilter, ChatLogStats
from app.services.chat_log_service import ChatLogService

router = APIRouter(prefix="/api/chat-logs", tags=["chat-logs"])


@router.get("", response_model=ChatLogListResponse)
async def list_chat_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    chatbot_id: int | None = None,
    conversation_id: int | None = None,
    message_id: int | None = None,
    llm_provider_id: int | None = None,
    model: str | None = None,
    status: str | None = None,
    use_rag: bool | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取聊天日志列表"""
    filter = ChatLogFilter(
        chatbot_id=chatbot_id,
        conversation_id=conversation_id,
        message_id=message_id,
        llm_provider_id=llm_provider_id,
        model=model,
        status=status,
        use_rag=use_rag,
        start_date=start_date,
        end_date=end_date
    )
    return await ChatLogService.list_logs(db, filter, skip, limit)


@router.get("/stats", response_model=ChatLogStats)
async def get_chat_log_stats(
    chatbot_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db)
):
    """获取日志统计信息"""
    filter = ChatLogFilter(
        chatbot_id=chatbot_id,
        start_date=start_date,
        end_date=end_date
    )
    return await ChatLogService.get_stats(db, filter)


@router.get("/{log_id}", response_model=ChatLogResponse)
async def get_chat_log(
    log_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取日志详情"""
    log = await ChatLogService.get_log(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Chat log not found")
    
    return ChatLogResponse(
        id=log.id,
        conversation_id=log.conversation_id,
        chatbot_id=log.chatbot_id,
        message_id=log.message_id,
        llm_provider_id=log.llm_provider_id,
        llm_provider_name=log.llm_provider_name,
        model=log.model,
        input_text=log.input_text,
        output_text=log.output_text,
        use_query_rewrite=log.use_query_rewrite,
        rewrite_time_ms=log.rewrite_time_ms,
        rewritten_query=log.rewritten_query,
        use_rag=log.use_rag,
        rag_query_time_ms=log.rag_query_time_ms,
        rag_results_count=log.rag_results_count,
        rag_results=log.rag_results,
        total_time_ms=log.total_time_ms,
        llm_time_ms=log.llm_time_ms,
        input_tokens=log.input_tokens,
        output_tokens=log.output_tokens,
        status=log.status,
        error_message=log.error_message,
        created_at=log.created_at,
        chatbot_name=log.chatbot.name if log.chatbot else None,
        conversation_title=log.conversation.title if log.conversation else None
    )


@router.delete("")
async def delete_chat_logs(
    before_date: datetime | None = None,
    chatbot_id: int | None = None,
    db: AsyncSession = Depends(get_db)
):
    """批量删除日志"""
    if not before_date and not chatbot_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one filter (before_date or chatbot_id)"
        )
    
    deleted_count = await ChatLogService.delete_logs(db, before_date, chatbot_id)
    return {"deleted_count": deleted_count}


