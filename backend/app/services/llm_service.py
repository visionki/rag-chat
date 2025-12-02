"""
LLM服务 - 管理不同LLM Provider的调用
"""
import json
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.models import LLMProvider
from app.schemas.provider import ProviderTestResponse
from app.logger import get_logger

logger = get_logger("rag-chat.llm")


class LLMService:
    """LLM服务"""
    
    def get_llm(
        self, 
        provider: LLMProvider, 
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        streaming: bool = False
    ) -> BaseChatModel:
        """
        根据Provider配置获取LLM实例
        """
        model_name = model
        if not model_name and provider.models:
            # 使用配置的第一个模型
            models = json.loads(provider.models)
            model_name = models[0] if models else None
        
        if not model_name:
            raise ValueError("No model specified")
        
        logger.debug(f"创建LLM实例: type={provider.provider_type}, model={model_name}")
        
        if provider.provider_type == "openai":
            return ChatOpenAI(
                base_url=provider.base_url,
                api_key=provider.api_key or "not-needed",
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming
            )
        elif provider.provider_type == "claude":
            return ChatAnthropic(
                api_key=provider.api_key,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming
            )
        elif provider.provider_type == "ollama":
            return ChatOllama(
                base_url=provider.base_url or "http://localhost:11434",
                model=model_name,
                temperature=temperature,
                num_predict=max_tokens
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider.provider_type}")
    
    async def test_provider(self, provider: LLMProvider) -> ProviderTestResponse:
        """
        测试Provider连接
        """
        logger.info(f"🔗 测试LLM连接: {provider.name} ({provider.provider_type})")
        
        try:
            llm = self.get_llm(provider, temperature=0)
            # 发送简单测试消息
            response = await llm.ainvoke([HumanMessage(content="Say 'OK' if you can hear me.")])
            
            # 获取可用模型列表
            models = []
            if provider.models:
                models = json.loads(provider.models)
            
            logger.info(f"✅ LLM连接成功: {provider.name}")
            return ProviderTestResponse(
                success=True,
                message=f"连接成功: {response.content[:100]}",
                models=models
            )
        except Exception as e:
            logger.error(f"❌ LLM连接失败: {provider.name} - {e}")
            return ProviderTestResponse(
                success=False,
                message=f"连接失败: {str(e)}"
            )
    
    async def chat(
        self,
        provider: LLMProvider,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        同步聊天
        """
        llm = self.get_llm(provider, model, temperature, max_tokens)
        
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        response = await llm.ainvoke(langchain_messages)
        return response.content
    
    async def chat_stream(
        self,
        provider: LLMProvider,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天
        """
        llm = self.get_llm(provider, model, temperature, max_tokens, streaming=True)
        
        langchain_messages = []
        for msg in messages:
            if msg["role"] == "system":
                langchain_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                langchain_messages.append(AIMessage(content=msg["content"]))
        
        async for chunk in llm.astream(langchain_messages):
            if chunk.content:
                yield chunk.content
