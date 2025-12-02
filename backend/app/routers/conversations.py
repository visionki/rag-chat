"""
会话管理API路由
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Chatbot, Conversation, Message
from app.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    ConversationListResponse, MessageResponse, ChatRequest, ChatResponse
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["conversations"])

chat_service = ChatService()


# ============ 会话管理 ============

@router.post("/chatbots/{chatbot_id}/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    chatbot_id: int,
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建会话"""
    # 检查Chatbot是否存在
    result = await db.execute(
        select(Chatbot).where(Chatbot.id == chatbot_id)
    )
    chatbot = result.scalar_one_or_none()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    conversation = Conversation(
        chatbot_id=chatbot_id,
        title=data.title or "新会话"
    )
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    
    return ConversationResponse(
        id=conversation.id,
        chatbot_id=conversation.chatbot_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
        last_message=None
    )


@router.get("/chatbots/{chatbot_id}/conversations", response_model=ConversationListResponse)
async def list_conversations(
    chatbot_id: int,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取Chatbot的会话列表"""
    # 获取总数
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.chatbot_id == chatbot_id)
    )
    total = count_result.scalar()
    
    # 获取列表
    query = (
        select(Conversation)
        .where(Conversation.chatbot_id == chatbot_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    items = []
    for conv in conversations:
        # 获取消息数量和最后一条消息
        msg_count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        msg_count = msg_count_result.scalar()
        
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()
        
        items.append(ConversationResponse(
            id=conv.id,
            chatbot_id=conv.chatbot_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
            last_message=last_msg.content[:100] if last_msg else None
        ))
    
    return ConversationListResponse(total=total, items=items)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取会话详情（包含消息）"""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationDetailResponse(
        id=conversation.id,
        chatbot_id=conversation.chatbot_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(conversation.messages),
        last_message=conversation.messages[-1].content[:100] if conversation.messages else None,
        messages=[MessageResponse.model_validate(msg) for msg in conversation.messages]
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除会话"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """获取会话消息"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()
    return [MessageResponse.model_validate(msg) for msg in messages]


# ============ 聊天 ============

@router.post("/conversations/{conversation_id}/chat")
async def chat(
    conversation_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """发送消息并获取回复"""
    # 获取会话（包含chatbot信息）
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.chatbot).selectinload(Chatbot.llm_provider),
            selectinload(Conversation.messages)
        )
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if not conversation.chatbot.llm_provider:
        raise HTTPException(
            status_code=400,
            detail="Chatbot has no LLM provider configured"
        )
    
    if request.stream:
        # 流式响应
        async def generate():
            generator = await chat_service.chat(
                db=db,
                conversation=conversation,
                user_message=request.message,
                stream=True
            )
            async for chunk in generator:
                # SSE格式
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    else:
        # 非流式响应
        response, sources = await chat_service.chat(
            db=db,
            conversation=conversation,
            user_message=request.message,
            stream=False
        )
        
        # 获取最新的助手消息
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.role == "assistant")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        assistant_msg = result.scalar_one()
        
        return ChatResponse(
            message=MessageResponse.model_validate(assistant_msg),
            sources=sources
        )


