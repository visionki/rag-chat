"""
Embedding服务 - 文本向量化
"""
import httpx
import numpy as np
from typing import List
from app.models import EmbeddingProvider
from app.logger import get_logger

logger = get_logger("rag-chat.embedding")


class EmbeddingService:
    """Embedding服务 - 支持多种Provider"""
    
    async def get_embeddings(
        self,
        provider: EmbeddingProvider,
        texts: List[str]
    ) -> np.ndarray:
        """
        获取文本向量
        
        Args:
            provider: Embedding Provider配置
            texts: 待编码的文本列表
            
        Returns:
            shape=(len(texts), dim) 的向量矩阵
        """
        if provider.provider_type == "siliconflow":
            return await self._siliconflow_embed(provider, texts)
        elif provider.provider_type == "openai":
            return await self._openai_embed(provider, texts)
        elif provider.provider_type == "ollama":
            return await self._ollama_embed(provider, texts)
        else:
            raise ValueError(f"不支持的provider类型: {provider.provider_type}")
    
    async def _siliconflow_embed(
        self,
        provider: EmbeddingProvider,
        texts: List[str],
        batch_size: int = 128
    ) -> np.ndarray:
        """
        SiliconFlow Embedding实现
        
        复用测试代码中验证有效的实现：
        - 模型：Qwen/Qwen3-Embedding-8B
        - 批次大小：128
        """
        if not provider.api_key:
            raise RuntimeError("SiliconFlow Provider未配置API Key")
        
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        base_url = provider.base_url or "https://api.siliconflow.cn/v1/embeddings"
        all_embeddings: List[List[float]] = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 分批处理，避免单次请求过大
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                logger.debug(f"🔢 正在向量化批次 {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                payload = {
                    "model": provider.model,
                    "input": batch_texts
                }
                
                try:
                    response = await client.post(base_url, headers=headers, json=payload)
                    
                    if response.status_code != 200:
                        raise RuntimeError(
                            f"SiliconFlow API调用失败: status={response.status_code}, "
                            f"body={response.text}"
                        )
                    
                    data = response.json()
                    
                    if "data" not in data:
                        raise RuntimeError(f"返回数据中没有 'data' 字段: {data}")
                    
                    batch_embeddings = [item["embedding"] for item in data["data"]]
                    
                    if len(batch_embeddings) != len(batch_texts):
                        raise RuntimeError(
                            f"返回的向量数量与输入文本数量不匹配: "
                            f"{len(batch_embeddings)} vs {len(batch_texts)}"
                        )
                    
                    all_embeddings.extend(batch_embeddings)
                    
                except httpx.RequestError as e:
                    raise RuntimeError(f"网络请求失败: {e}")
        
        embeddings = np.array(all_embeddings, dtype=np.float32)
        logger.info(f"✅ 向量化完成: {len(texts)} 个文本 -> {embeddings.shape}")
        
        return embeddings
    
    async def _openai_embed(
        self,
        provider: EmbeddingProvider,
        texts: List[str],
        batch_size: int = 100
    ) -> np.ndarray:
        """OpenAI Embedding实现"""
        if not provider.api_key:
            raise RuntimeError("OpenAI Provider未配置API Key")
        
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建完整URL
        base_url = provider.base_url or "https://api.openai.com/v1"
        # 如果base_url已经包含/embeddings，不重复添加
        if not base_url.endswith('/embeddings'):
            if base_url.endswith('/v1'):
                embeddings_url = f"{base_url}/embeddings"
            else:
                embeddings_url = f"{base_url}/v1/embeddings"
        else:
            embeddings_url = base_url
        
        logger.debug(f"🔗 OpenAI Embedding URL: {embeddings_url}")
        
        all_embeddings: List[List[float]] = []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                payload = {
                    "model": provider.model,
                    "input": batch_texts
                }
                
                try:
                    response = await client.post(embeddings_url, headers=headers, json=payload)
                    
                    if response.status_code != 200:
                        raise RuntimeError(
                            f"OpenAI API调用失败: status={response.status_code}, "
                            f"url={embeddings_url}, response={response.text}"
                        )
                    
                    data = response.json()
                    batch_embeddings = [item["embedding"] for item in data["data"]]
                    all_embeddings.extend(batch_embeddings)
                    
                except httpx.RequestError as e:
                    raise RuntimeError(f"网络请求失败: {e}")
        
        return np.array(all_embeddings, dtype=np.float32)
    
    async def _ollama_embed(
        self,
        provider: EmbeddingProvider,
        texts: List[str]
    ) -> np.ndarray:
        """Ollama Embedding实现（本地模型）"""
        base_url = provider.base_url or "http://localhost:11434"
        all_embeddings: List[List[float]] = []
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            for text in texts:
                response = await client.post(
                    f"{base_url}/api/embeddings",
                    json={
                        "model": provider.model,
                        "prompt": text
                    }
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"Ollama API调用失败: {response.text}")
                
                data = response.json()
                all_embeddings.append(data["embedding"])
        
        return np.array(all_embeddings, dtype=np.float32)
    
    async def test_provider(self, provider: EmbeddingProvider) -> dict:
        """
        测试Provider连接
        
        Returns:
            {
                "success": bool,
                "message": str,
                "dimensions": int | None
            }
        """
        try:
            # 测试向量化
            test_text = ["这是一个测试文本"]
            embeddings = await self.get_embeddings(provider, test_text)
            
            return {
                "success": True,
                "message": f"连接成功，向量维度: {embeddings.shape[1]}",
                "dimensions": int(embeddings.shape[1])
            }
        except Exception as e:
            logger.error(f"❌ Provider测试失败: {e}")
            return {
                "success": False,
                "message": f"连接失败: {str(e)}",
                "dimensions": None
            }


