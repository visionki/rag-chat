"""
聊天服务 - RAG问答
"""
import json
import time
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import (
    Chatbot,
    Conversation,
    Message,
    LLMProvider,
    EmbeddingProvider,
)
from app.services.llm_service import LLMService
from app.services.vectorstore_service import VectorStoreService
from app.services.chat_log_service import ChatLogService
from app.logger import get_logger

logger = get_logger("rag-chat.chat")


class ChatService:
    """聊天服务"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.vectorstore_service = VectorStoreService()
    
    async def get_default_embedding_provider(self, db: AsyncSession) -> EmbeddingProvider | None:
        """获取默认Embedding Provider"""
        result = await db.execute(
            select(EmbeddingProvider)
            .where(EmbeddingProvider.is_default == True, EmbeddingProvider.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def _rewrite_query(
        self,
        conversation: Conversation,
        user_message: str,
        rewrite_provider: LLMProvider,
        rewrite_model: str | None
    ) -> str | None:
        """
        使用LLM重写查询，使其更适合检索
        """
        # 构建最近2-3轮对话历史
        recent_messages = conversation.messages[-6:]  # 最多3轮对话（6条消息）
        
        history_text = ""
        for msg in recent_messages:
            role_name = "用户" if msg.role == "user" else "助手"
            history_text += f"{role_name}: {msg.content}\n"
        
        rewrite_prompt = f"""你是一个查询重写助手。请分析用户最新问题是否需要依赖对话历史来理解，然后进行适当处理。

判断标准：
- 如果问题包含指代词（如"它"、"这个"、"他的"等）或省略主语，需要从历史中补充
- 如果问题本身已经完整独立、不依赖上下文就能理解，则保持原样或仅做轻微优化

要求：
1. 只有在问题确实依赖上下文时才补充信息
2. 不要强行将历史话题整合到独立的新问题中
3. 解决真正的指代问题（代词→具体名词）
4. 保持查询简洁明确，适合检索
5. 只输出改写后的查询，不要有任何解释

示例：
- 历史讨论"Claude 4.5 Opus" → 用户问"它支持多模态吗" → 重写为"Claude 4.5 Opus支持多模态吗"（补充指代）
- 历史讨论"Claude 4.5 Opus" → 用户问"有哪些被废弃了的模型" → 保持"有哪些被废弃了的模型"（独立问题，不补充）

{f"对话历史：{chr(10)}{history_text}" if history_text else ""}
用户最新问题：{user_message}

改写后的查询："""

        try:
            response = await self.llm_service.chat(
                provider=rewrite_provider,
                messages=[{"role": "user", "content": rewrite_prompt}],
                model=rewrite_model,
                temperature=0.1,  # 低温度，更确定性
                max_tokens=200   # 查询不需要太长
            )
            
            # 清理响应
            rewritten = response.strip()
            # 移除可能的引号
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            if rewritten.startswith("'") and rewritten.endswith("'"):
                rewritten = rewritten[1:-1]
            
            return rewritten if rewritten else None
        except Exception as e:
            logger.error(f"查询重写失败: {e}")
            return None
    
    async def chat(
        self,
        db: AsyncSession,
        conversation: Conversation,
        user_message: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None] | tuple[str, list[dict]]:
        """
        聊天（支持RAG检索）
        """
        start_time = time.time()
        chatbot = conversation.chatbot
        
        logger.info(f"💬 收到聊天请求: Bot={chatbot.name}, 会话ID={conversation.id}")
        logger.info(f"   用户: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        
        # 获取LLM Provider
        if not chatbot.llm_provider:
            logger.error("❌ Chatbot未配置LLM Provider")
            raise ValueError("Chatbot has no LLM provider configured")
        
        # 构建消息列表
        messages = []
        
        # 系统提示
        system_prompt = chatbot.system_prompt or "你是一个有用的AI助手。"
        
        # 日志相关变量
        rag_start_time = None
        rag_time_ms = None
        sources = []
        use_rag = chatbot.use_knowledge_base
        
        # 查询重写相关变量
        use_query_rewrite = bool(chatbot.use_query_rewrite and chatbot.rewrite_provider)
        rewrite_time_ms = None
        rewritten_query = None
        rag_query = user_message  # 默认使用原始查询
        
        # 🔄 如果启用查询重写，先重写查询
        if use_query_rewrite and use_rag:
            rewrite_start_time = time.time()
            try:
                rewritten_query = await self._rewrite_query(
                    conversation=conversation,
                    user_message=user_message,
                    rewrite_provider=chatbot.rewrite_provider,
                    rewrite_model=chatbot.rewrite_model
                )
                rewrite_time_ms = int((time.time() - rewrite_start_time) * 1000)
                
                if rewritten_query and rewritten_query != user_message:
                    rag_query = rewritten_query
                    logger.info(f"✏️ 查询重写完成 ({rewrite_time_ms}ms)")
                    logger.info(f"   原始: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
                    logger.info(f"   重写: {rewritten_query[:50]}{'...' if len(rewritten_query) > 50 else ''}")
                else:
                    logger.info(f"✏️ 查询无需重写 ({rewrite_time_ms}ms)")
                    rewritten_query = None  # 如果没有变化，不记录
            except Exception as e:
                rewrite_time_ms = int((time.time() - rewrite_start_time) * 1000)
                logger.warning(f"⚠️ 查询重写失败 ({rewrite_time_ms}ms): {e}")
                # 重写失败不影响后续流程，使用原始查询
        
        # 🔥 如果启用知识库，进行RAG检索
        if use_rag:
            embedding_provider = await self.get_default_embedding_provider(db)
            if embedding_provider:
                logger.info(f"🔍 开始RAG检索... (Embedding: {embedding_provider.name})")
                rag_start_time = time.time()
                
                try:
                    # 使用余弦相似度检索（使用重写后的查询或原始查询）
                    docs_with_scores = await self.vectorstore_service.similarity_search_with_score(
                        embedding_provider=embedding_provider,
                        query=rag_query,  # 使用可能重写过的查询
                        k=chatbot.top_k,
                    )
                    
                    rag_time_ms = int((time.time() - rag_start_time) * 1000)
                    logger.info(f"✅ RAG检索完成: 找到 {len(docs_with_scores)} 个相关文档 ({rag_time_ms}ms)")
                    
                    if docs_with_scores:
                        # 构建上下文
                        context_parts = []
                        for doc, score in docs_with_scores:
                            context_parts.append(doc.page_content)
                            sources.append(
                                {
                                    "document_id": doc.metadata.get("document_id"),
                                    "filename": doc.metadata.get("filename"),
                                    "chunk_index": doc.metadata.get("chunk_index"),
                                    "content": doc.page_content,  # 保存完整内容，方便校验
                                    "score": float(score),
                                }
                            )
                            logger.debug(
                                f"   - {doc.metadata.get('filename')} "
                                f"[chunk {doc.metadata.get('chunk_index')}]: "
                                f"score={score:.4f}"
                            )
                        
                        context = "\n\n---\n\n".join(context_parts)
                        system_prompt += (
                            "\n\n请基于以下参考资料回答问题。如果资料中没有相关信息，请如实告知。\n\n参考资料：\n"
                            f"{context}"
                        )
                        
                        logger.info(f"📚 已构建上下文: {len(context_parts)} 个文档片段")
                    else:
                        logger.warning("⚠️  未检索到相关文档")
                
                except Exception as e:
                    logger.error(f"❌ RAG检索失败: {e}", exc_info=True)
                    # RAG失败不影响对话，继续使用基础LLM
            else:
                logger.warning("⚠️  未配置默认Embedding Provider，跳过RAG检索")
        
        messages.append({"role": "system", "content": system_prompt})
        
        # 历史消息（最近10条）
        history_count = len(conversation.messages[-10:])
        if history_count > 0:
            logger.debug(f"📜 加载历史消息: {history_count} 条")
        for msg in conversation.messages[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        # 当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 保存用户消息
        user_msg = Message(
            conversation_id=conversation.id,
            role="user",
            content=user_message
        )
        db.add(user_msg)
        await db.flush()
        
        logger.info(f"🤖 调用LLM: {chatbot.llm_provider.name} / {chatbot.model}")
        
        if stream:
            # 流式响应
            async def generate():
                llm_start_time = time.time()
                full_response = ""
                error_occurred = False
                error_message = None
                
                try:
                    async for chunk in self.llm_service.chat_stream(
                        provider=chatbot.llm_provider,
                        messages=messages,
                        model=chatbot.model,
                        temperature=chatbot.temperature,
                        max_tokens=chatbot.max_tokens
                    ):
                        full_response += chunk
                        yield chunk
                except Exception as e:
                    error_occurred = True
                    error_message = str(e)
                    logger.error(f"❌ LLM调用失败: {e}")
                    raise
                finally:
                    llm_time_ms = int((time.time() - llm_start_time) * 1000)
                    total_time_ms = int((time.time() - start_time) * 1000)
                    
                    # 保存助手消息
                    assistant_msg_id = None
                    if full_response:
                        assistant_msg = Message(
                            conversation_id=conversation.id,
                            role="assistant",
                            content=full_response,
                            sources=json.dumps(sources) if sources else None
                        )
                        db.add(assistant_msg)
                        await db.flush()
                        assistant_msg_id = assistant_msg.id
                    
                    # 更新会话标题（如果是第一条消息）
                    if len(conversation.messages) <= 2:
                        conversation.title = user_message[:50]
                        await db.flush()
                    
                    # 记录日志（关联助手消息ID）
                    await ChatLogService.create_log(
                        db=db,
                        conversation_id=conversation.id,
                        chatbot_id=chatbot.id,
                        llm_provider_id=chatbot.llm_provider_id,
                        llm_provider_name=chatbot.llm_provider.name if chatbot.llm_provider else None,
                        model=chatbot.model,
                        input_text=user_message,
                        output_text=full_response if full_response else None,
                        system_prompt=system_prompt,
                        use_query_rewrite=use_query_rewrite,
                        rewrite_time_ms=rewrite_time_ms,
                        rewritten_query=rewritten_query,
                        use_rag=use_rag,
                        rag_query_time_ms=rag_time_ms,
                        rag_results_count=len(sources) if sources else None,
                        rag_results=sources if sources else None,
                        total_time_ms=total_time_ms,
                        llm_time_ms=llm_time_ms,
                        status="error" if error_occurred else "success",
                        error_message=error_message,
                        message_id=assistant_msg_id
                    )
                    await db.flush()
                    
                    if not error_occurred:
                        response_preview = full_response[:50] + "..." if len(full_response) > 50 else full_response
                        logger.info(f"✅ 回复完成: {response_preview}")
                        logger.info(f"   耗时: 总计={total_time_ms}ms, LLM={llm_time_ms}ms, RAG={rag_time_ms or 0}ms, 重写={rewrite_time_ms or 0}ms")
            
            return generate()
        else:
            # 非流式响应
            llm_start_time = time.time()
            error_occurred = False
            error_message = None
            response = ""
            
            try:
                response = await self.llm_service.chat(
                    provider=chatbot.llm_provider,
                    messages=messages,
                    model=chatbot.model,
                    temperature=chatbot.temperature,
                    max_tokens=chatbot.max_tokens
                )
            except Exception as e:
                error_occurred = True
                error_message = str(e)
                logger.error(f"❌ LLM调用失败: {e}")
                raise
            finally:
                llm_time_ms = int((time.time() - llm_start_time) * 1000)
                total_time_ms = int((time.time() - start_time) * 1000)
            
            # 保存助手消息
            assistant_msg = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=response,
                sources=json.dumps(sources) if sources else None
            )
            db.add(assistant_msg)
            await db.flush()
            
            # 记录日志（关联助手消息ID）
            await ChatLogService.create_log(
                db=db,
                conversation_id=conversation.id,
                chatbot_id=chatbot.id,
                llm_provider_id=chatbot.llm_provider_id,
                llm_provider_name=chatbot.llm_provider.name if chatbot.llm_provider else None,
                model=chatbot.model,
                input_text=user_message,
                output_text=response if response else None,
                system_prompt=system_prompt,
                use_query_rewrite=use_query_rewrite,
                rewrite_time_ms=rewrite_time_ms,
                rewritten_query=rewritten_query,
                use_rag=use_rag,
                rag_query_time_ms=rag_time_ms,
                rag_results_count=len(sources) if sources else None,
                rag_results=sources if sources else None,
                total_time_ms=total_time_ms,
                llm_time_ms=llm_time_ms,
                status="error" if error_occurred else "success",
                error_message=error_message,
                message_id=assistant_msg.id
            )
            
            # 更新会话标题
            if len(conversation.messages) <= 2:
                conversation.title = user_message[:50]
                await db.flush()
            
            response_preview = response[:50] + "..." if len(response) > 50 else response
            logger.info(f"✅ 回复完成: {response_preview}")
            logger.info(f"   耗时: 总计={total_time_ms}ms, LLM={llm_time_ms}ms, RAG={rag_time_ms or 0}ms, 重写={rewrite_time_ms or 0}ms")
            
            return response, sources
