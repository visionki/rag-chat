"""
聊天日志服务
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.chat_log import ChatLog
from app.schemas.chat_log import ChatLogResponse, ChatLogListResponse, ChatLogFilter, ChatLogStats


class ChatLogService:
    """聊天日志服务"""
    
    @staticmethod
    async def create_log(
        db: AsyncSession,
        conversation_id: int | None,
        chatbot_id: int | None,
        llm_provider_id: int | None,
        llm_provider_name: str | None,
        model: str | None,
        input_text: str,
        output_text: str | None = None,
        system_prompt: str | None = None,
        use_query_rewrite: bool = False,
        rewrite_time_ms: int | None = None,
        rewritten_query: str | None = None,
        use_rag: bool = False,
        rag_query_time_ms: int | None = None,
        rag_results_count: int | None = None,
        rag_results: list[dict] | None = None,
        total_time_ms: int | None = None,
        llm_time_ms: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        status: str = "success",
        error_message: str | None = None,
        message_id: int | None = None
    ) -> ChatLog:
        """创建日志记录"""
        log = ChatLog(
            conversation_id=conversation_id,
            chatbot_id=chatbot_id,
            message_id=message_id,
            llm_provider_id=llm_provider_id,
            llm_provider_name=llm_provider_name,
            model=model,
            input_text=input_text,
            output_text=output_text,
            system_prompt=system_prompt,
            use_query_rewrite=use_query_rewrite,
            rewrite_time_ms=rewrite_time_ms,
            rewritten_query=rewritten_query,
            use_rag=use_rag,
            rag_query_time_ms=rag_query_time_ms,
            rag_results_count=rag_results_count,
            rag_results=json.dumps(rag_results, ensure_ascii=False) if rag_results else None,
            total_time_ms=total_time_ms,
            llm_time_ms=llm_time_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            status=status,
            error_message=error_message
        )
        db.add(log)
        await db.flush()
        return log
    
    @staticmethod
    async def list_logs(
        db: AsyncSession,
        filter: ChatLogFilter | None = None,
        skip: int = 0,
        limit: int = 50
    ) -> ChatLogListResponse:
        """获取日志列表"""
        query = select(ChatLog)
        count_query = select(func.count(ChatLog.id))
        
        # 应用筛选条件
        conditions = []
        if filter:
            if filter.chatbot_id:
                conditions.append(ChatLog.chatbot_id == filter.chatbot_id)
            if filter.conversation_id:
                conditions.append(ChatLog.conversation_id == filter.conversation_id)
            if filter.message_id:
                conditions.append(ChatLog.message_id == filter.message_id)
            if filter.llm_provider_id:
                conditions.append(ChatLog.llm_provider_id == filter.llm_provider_id)
            if filter.model:
                conditions.append(ChatLog.model == filter.model)
            if filter.status:
                conditions.append(ChatLog.status == filter.status)
            if filter.use_rag is not None:
                conditions.append(ChatLog.use_rag == filter.use_rag)
            if filter.start_date:
                conditions.append(ChatLog.created_at >= filter.start_date)
            if filter.end_date:
                conditions.append(ChatLog.created_at <= filter.end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取列表
        query = query.order_by(ChatLog.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # 构建响应
        items = []
        for log in logs:
            item = ChatLogResponse(
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
            items.append(item)
        
        return ChatLogListResponse(total=total, items=items)
    
    @staticmethod
    async def get_log(db: AsyncSession, log_id: int) -> ChatLog | None:
        """获取日志详情"""
        result = await db.execute(
            select(ChatLog).where(ChatLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_stats(
        db: AsyncSession,
        filter: ChatLogFilter | None = None
    ) -> ChatLogStats:
        """获取日志统计"""
        base_query = select(ChatLog)
        
        # 应用筛选条件
        conditions = []
        if filter:
            if filter.chatbot_id:
                conditions.append(ChatLog.chatbot_id == filter.chatbot_id)
            if filter.start_date:
                conditions.append(ChatLog.created_at >= filter.start_date)
            if filter.end_date:
                conditions.append(ChatLog.created_at <= filter.end_date)
        
        where_clause = and_(*conditions) if conditions else True
        
        # 总请求数
        total_result = await db.execute(
            select(func.count(ChatLog.id)).where(where_clause)
        )
        total_requests = total_result.scalar() or 0
        
        # 成功/失败数
        success_result = await db.execute(
            select(func.count(ChatLog.id)).where(
                and_(where_clause, ChatLog.status == "success")
            )
        )
        success_count = success_result.scalar() or 0
        error_count = total_requests - success_count
        
        # 平均时间
        avg_total_result = await db.execute(
            select(func.avg(ChatLog.total_time_ms)).where(
                and_(where_clause, ChatLog.total_time_ms.isnot(None))
            )
        )
        avg_total_time_ms = avg_total_result.scalar()
        
        avg_rag_result = await db.execute(
            select(func.avg(ChatLog.rag_query_time_ms)).where(
                and_(where_clause, ChatLog.rag_query_time_ms.isnot(None))
            )
        )
        avg_rag_time_ms = avg_rag_result.scalar()
        
        avg_llm_result = await db.execute(
            select(func.avg(ChatLog.llm_time_ms)).where(
                and_(where_clause, ChatLog.llm_time_ms.isnot(None))
            )
        )
        avg_llm_time_ms = avg_llm_result.scalar()
        
        # Token统计
        input_tokens_result = await db.execute(
            select(func.sum(ChatLog.input_tokens)).where(
                and_(where_clause, ChatLog.input_tokens.isnot(None))
            )
        )
        total_input_tokens = input_tokens_result.scalar() or 0
        
        output_tokens_result = await db.execute(
            select(func.sum(ChatLog.output_tokens)).where(
                and_(where_clause, ChatLog.output_tokens.isnot(None))
            )
        )
        total_output_tokens = output_tokens_result.scalar() or 0
        
        return ChatLogStats(
            total_requests=total_requests,
            success_count=success_count,
            error_count=error_count,
            avg_total_time_ms=round(avg_total_time_ms, 2) if avg_total_time_ms else None,
            avg_rag_time_ms=round(avg_rag_time_ms, 2) if avg_rag_time_ms else None,
            avg_llm_time_ms=round(avg_llm_time_ms, 2) if avg_llm_time_ms else None,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens
        )
    
    @staticmethod
    async def delete_logs(
        db: AsyncSession,
        before_date: datetime | None = None,
        chatbot_id: int | None = None
    ) -> int:
        """批量删除日志"""
        from sqlalchemy import delete
        
        conditions = []
        if before_date:
            conditions.append(ChatLog.created_at < before_date)
        if chatbot_id:
            conditions.append(ChatLog.chatbot_id == chatbot_id)
        
        if not conditions:
            return 0
        
        stmt = delete(ChatLog).where(and_(*conditions))
        result = await db.execute(stmt)
        return result.rowcount


