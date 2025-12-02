"""
Chatbot管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Chatbot, Conversation
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse, ChatbotListResponse

router = APIRouter(prefix="/api/chatbots", tags=["chatbots"])


@router.post("", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    data: ChatbotCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建Chatbot"""
    chatbot = Chatbot(**data.model_dump())
    db.add(chatbot)
    await db.flush()
    await db.refresh(chatbot)
    
    return ChatbotResponse(
        **data.model_dump(),
        id=chatbot.id,
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
        conversation_count=0
    )


@router.get("", response_model=ChatbotListResponse)
async def list_chatbots(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取Chatbot列表"""
    # 获取总数
    count_result = await db.execute(select(func.count(Chatbot.id)))
    total = count_result.scalar()
    
    # 获取列表，包含会话数量
    query = (
        select(Chatbot)
        .order_by(Chatbot.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    chatbots = result.scalars().all()
    
    # 获取每个chatbot的会话数量
    items = []
    for chatbot in chatbots:
        conv_count_result = await db.execute(
            select(func.count(Conversation.id)).where(Conversation.chatbot_id == chatbot.id)
        )
        conv_count = conv_count_result.scalar()
        
        items.append(ChatbotResponse(
            id=chatbot.id,
            name=chatbot.name,
            description=chatbot.description,
            system_prompt=chatbot.system_prompt,
            llm_provider_id=chatbot.llm_provider_id,
            model=chatbot.model,
            temperature=chatbot.temperature,
            max_tokens=chatbot.max_tokens,
            use_knowledge_base=chatbot.use_knowledge_base,
            top_k=chatbot.top_k,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at,
            conversation_count=conv_count
        ))
    
    return ChatbotListResponse(total=total, items=items)


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取Chatbot详情"""
    result = await db.execute(
        select(Chatbot).where(Chatbot.id == chatbot_id)
    )
    chatbot = result.scalar_one_or_none()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # 获取会话数量
    conv_count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.chatbot_id == chatbot.id)
    )
    conv_count = conv_count_result.scalar()
    
    return ChatbotResponse(
        id=chatbot.id,
        name=chatbot.name,
        description=chatbot.description,
        system_prompt=chatbot.system_prompt,
        llm_provider_id=chatbot.llm_provider_id,
        model=chatbot.model,
        temperature=chatbot.temperature,
        max_tokens=chatbot.max_tokens,
        use_knowledge_base=chatbot.use_knowledge_base,
        top_k=chatbot.top_k,
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
        conversation_count=conv_count
    )


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: int,
    data: ChatbotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新Chatbot"""
    result = await db.execute(
        select(Chatbot).where(Chatbot.id == chatbot_id)
    )
    chatbot = result.scalar_one_or_none()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(chatbot, key, value)
    
    await db.flush()
    await db.refresh(chatbot)
    
    # 获取会话数量
    conv_count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.chatbot_id == chatbot.id)
    )
    conv_count = conv_count_result.scalar()
    
    return ChatbotResponse(
        id=chatbot.id,
        name=chatbot.name,
        description=chatbot.description,
        system_prompt=chatbot.system_prompt,
        llm_provider_id=chatbot.llm_provider_id,
        model=chatbot.model,
        temperature=chatbot.temperature,
        max_tokens=chatbot.max_tokens,
        use_knowledge_base=chatbot.use_knowledge_base,
        top_k=chatbot.top_k,
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
        conversation_count=conv_count
    )


@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(
    chatbot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除Chatbot"""
    result = await db.execute(
        select(Chatbot).where(Chatbot.id == chatbot_id)
    )
    chatbot = result.scalar_one_or_none()
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    await db.delete(chatbot)


