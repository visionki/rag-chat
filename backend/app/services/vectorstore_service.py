"""
向量存储服务 - 基于ChromaDB
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
import numpy as np
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from app.config import settings
from app.models import EmbeddingProvider
from app.services.embedding_service import EmbeddingService
from app.logger import get_logger

logger = get_logger("rag-chat.vectorstore")


class VectorStoreService:
    """
    向量存储服务
    
    特性：
    - 使用ChromaDB持久化存储
    - 使用余弦距离（cosine）进行相似度计算
    - 支持按文档ID过滤
    - 使用HNSW索引加速检索
    """
    
    COLLECTION_NAME = "documents"
    
    def __init__(self):
        """初始化ChromaDB客户端"""
        # 确保目录存在
        chroma_dir = Path(settings.CHROMA_DIR)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建持久化客户端
        self.client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )
        
        self.embedding_service = EmbeddingService()
        
        logger.info(f"📁 ChromaDB初始化完成: {chroma_dir}")
    
    def get_or_create_collection(self):
        """
        获取或创建collection
        
        关键配置：
        - hnsw:space = cosine：使用余弦距离（归一化，只看方向）
        - hnsw:construction_ef = 100：构建索引时的搜索范围
        - hnsw:M = 16：HNSW图的连接数
        """
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "hnsw:space": "cosine",  # 🔥 使用余弦距离，适合文本语义检索
                "hnsw:construction_ef": 100,
                "hnsw:M": 16
            }
        )
    
    async def add_documents(
        self,
        embedding_provider: EmbeddingProvider,
        document_id: int,
        chunks: List[str],
        metadatas: List[Dict]
    ):
        """
        添加文档向量到向量库
        
        Args:
            embedding_provider: Embedding配置
            document_id: 文档ID
            chunks: 文本分块列表
            metadatas: 元数据列表（需包含document_id, filename, chunk_index）
        """
        if not chunks:
            raise ValueError("chunks不能为空")
        
        logger.info(f"🔢 开始向量化: {len(chunks)} 个分块")
        
        # 1. 生成向量
        embeddings = await self.embedding_service.get_embeddings(
            embedding_provider, chunks
        )
        
        logger.info(f"✅ 向量化完成: shape={embeddings.shape}")
        
        # 2. 添加到ChromaDB
        collection = self.get_or_create_collection()
        
        # 生成唯一ID
        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
        
        # 批量添加
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"💾 已添加 {len(chunks)} 个向量到ChromaDB")
    
    async def similarity_search_with_score(
        self,
        embedding_provider: EmbeddingProvider,
        query: str,
        k: int = 5,
        document_ids: Optional[List[int]] = None
    ) -> List[Tuple[object, float]]:
        """
        向量相似度检索
        
        Args:
            embedding_provider: Embedding配置
            query: 查询文本
            k: 返回top-k个结果
            document_ids: 可选，只在指定文档中检索
            
        Returns:
            List[(Document对象, 相似度分数)]
            - Document对象包含：page_content, metadata
            - 相似度分数：0-1之间，越大越相似（余弦相似度）
        """
        # 1. 查询向量化
        logger.debug(f"🔍 向量化查询: {query[:50]}...")
        query_embedding = await self.embedding_service.get_embeddings(
            embedding_provider, [query]
        )
        
        # 2. 构建过滤条件
        where = None
        if document_ids:
            where = {"document_id": {"$in": document_ids}}
        
        # 3. 检索
        collection = self.get_or_create_collection()
        results = collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # 4. 转换结果
        if not results["documents"] or not results["documents"][0]:
            logger.warning("⚠️  未检索到任何结果")
            return []
        
        chunks = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        
        # 🔥 余弦距离转余弦相似度：similarity = 1 - distance
        # ChromaDB的cosine距离范围[0, 2]，转为相似度[1, -1]（通常在[0.5, 1]）
        similarities = [1 - dist for dist in distances]
        
        # 5. 构造Document对象（兼容旧代码的langchain格式）
        from langchain_core.documents import Document
        
        documents_with_scores = []
        for chunk, similarity, metadata in zip(chunks, similarities, metadatas):
            doc = Document(
                page_content=chunk,
                metadata=metadata
            )
            documents_with_scores.append((doc, similarity))
        
        logger.info(f"✅ 检索完成: 返回 {len(documents_with_scores)} 个结果")
        
        return documents_with_scores
    
    async def delete_documents(self, document_id: int):
        """
        删除文档的所有向量
        
        Args:
            document_id: 文档ID
        """
        collection = self.get_or_create_collection()
        
        # 按metadata过滤删除
        collection.delete(
            where={"document_id": document_id}
        )
        
        logger.info(f"🗑️  已删除文档 {document_id} 的所有向量")
    
    def get_collection_stats(self) -> dict:
        """
        获取向量库统计信息
        
        Returns:
            {
                "total_vectors": int,
                "collection_name": str
            }
        """
        try:
            collection = self.get_or_create_collection()
            count = collection.count()
            
            return {
                "total_vectors": count,
                "collection_name": self.COLLECTION_NAME
            }
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {
                "total_vectors": 0,
                "collection_name": self.COLLECTION_NAME
            }
    
    def reset_collection(self):
        """
        清空并重建collection
        
        ⚠️  危险操作：会删除所有向量数据！
        用于：
        - 切换距离度量方式
        - 清空测试数据
        """
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
            logger.warning(f"🗑️  已删除collection: {self.COLLECTION_NAME}")
        except Exception:
            pass
        
        collection = self.get_or_create_collection()
        logger.info(f"✅ 已重建collection: {self.COLLECTION_NAME}")
        
        return collection


