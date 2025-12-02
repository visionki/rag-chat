"""
文档服务 - 处理文档上传、解析、向量化
"""
import uuid
import aiofiles
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.config import settings
from app.models import Document, EmbeddingProvider
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentUploadResponse
from app.utils.file_parser import FileParser
from app.utils.text_splitter import get_text_splitter
from app.services.vectorstore_service import VectorStoreService
from app.logger import get_logger

logger = get_logger("rag-chat.document")


class DocumentService:
    """文档服务"""
    
    def __init__(self):
        self.vectorstore_service = VectorStoreService()
    
    async def upload_document(
        self,
        db: AsyncSession,
        filename: str,
        content: bytes
    ) -> DocumentUploadResponse:
        """
        上传文档
        """
        logger.info(f"📄 开始上传文档: {filename}")
        
        # 检查文件类型
        if not FileParser.is_supported(filename):
            logger.warning(f"❌ 不支持的文件类型: {filename}")
            raise ValueError(f"Unsupported file type: {filename}")
        
        # 生成存储路径
        file_ext = Path(filename).suffix
        stored_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = settings.UPLOAD_DIR / stored_filename
        
        # 保存文件
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        file_size_kb = len(content) / 1024
        logger.info(f"💾 文件已保存: {stored_filename} ({file_size_kb:.1f} KB)")
        
        # 计算哈希
        content_hash = FileParser.compute_hash(content)
        
        # 创建文档记录
        document = Document(
            filename=filename,
            file_path=str(file_path),
            file_type=FileParser.get_file_type(filename),
            file_size=len(content),
            content_hash=content_hash,
            status="pending"
        )
        
        db.add(document)
        await db.flush()
        await db.refresh(document)
        
        logger.info(f"✅ 文档记录已创建: ID={document.id}, 状态=pending")
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            message="文档上传成功，等待处理"
        )
    
    async def process_document(
        self,
        db: AsyncSession,
        document_id: int
    ) -> Document:
        """
        处理文档 - 解析、分块、向量化
        
        使用测试代码验证的配置：
        - chunk_size: 1000
        - chunk_overlap: 200
        - is_markdown: True（对markdown文件）
        """
        logger.info(f"⚙️  开始处理文档: ID={document_id}")
        
        # 获取文档
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if not document:
            logger.error(f"❌ 文档不存在: ID={document_id}")
            raise ValueError("Document not found")
        
        # 获取默认Embedding Provider
        result = await db.execute(
            select(EmbeddingProvider).where(
                EmbeddingProvider.is_default == True,
                EmbeddingProvider.is_active == True
            )
        )
        embedding_provider = result.scalar_one_or_none()
        
        if not embedding_provider:
            error_msg = "未配置默认Embedding Provider"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        try:
            # 更新状态
            document.status = "processing"
            await db.flush()
            logger.info(f"📖 正在解析文档: {document.filename}")
            
            # 1. 解析文档
            file_path = Path(document.file_path)
            content = await FileParser.parse(file_path)
            
            content_length = len(content)
            logger.info(f"📝 文档解析完成: 提取 {content_length} 字符")
            
            # 2. 文本分块 - 使用测试代码的配置
            is_markdown = self._is_markdown_document(document, content)
            
            # 🔥 使用测试代码中验证有效的参数
            chunk_size = 1000
            chunk_overlap = 200
            
            splitter = get_text_splitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                is_markdown=is_markdown
            )
            chunks = splitter.split_text(content)
            
            if is_markdown:
                logger.info(f"📑 使用Markdown感知分块（size={chunk_size}, overlap={chunk_overlap}）")
            else:
                logger.info(f"📄 使用普通分块（size={chunk_size}, overlap={chunk_overlap}）")
            
            if not chunks:
                raise ValueError("No content extracted from document")
            
            logger.info(f"✂️  文本分块完成: {len(chunks)} 个块")
            
            # 3. 准备元数据
            metadatas = [
                {
                    "document_id": document.id,
                    "filename": document.filename,
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            
            # 4. 向量化并存储
            logger.info(f"🔢 正在向量化并存储到ChromaDB... (使用 {embedding_provider.name})")
            await self.vectorstore_service.add_documents(
                embedding_provider=embedding_provider,
                document_id=document.id,
                chunks=chunks,
                metadatas=metadatas
            )
            
            # 5. 更新文档状态
            document.status = "completed"
            document.chunk_count = len(chunks)
            document.embedding_provider_id = embedding_provider.id
            await db.flush()
            
            logger.info(f"✅ 文档处理完成: {document.filename} ({len(chunks)} 个向量)")
            
            return document
            
        except Exception as e:
            document.status = "failed"
            document.error_message = str(e)
            await db.flush()
            logger.error(f"❌ 文档处理失败: {document.filename} - {e}")
            raise
    
    def _is_markdown_document(self, document: Document, content: str) -> bool:
        """
        判断是否为Markdown文档
        
        判断依据：
        1. 文件扩展名是.md
        2. 文件类型是markdown或text
        3. 内容中包含Markdown标记
        """
        # 检查扩展名
        if document.filename.lower().endswith(".md"):
            return True
        
        # 检查文件类型
        if document.file_type not in ("markdown", "text"):
            return False
        
        # 检查内容特征（前1000字符）
        preview = content[:1000]
        markdown_markers = ["###", "##", "- ", "* ", "```", "**"]
        
        marker_count = sum(1 for marker in markdown_markers if marker in preview)
        
        # 如果包含2个以上Markdown标记，认为是Markdown
        return marker_count >= 2
    
    async def get_document(self, db: AsyncSession, document_id: int) -> Document | None:
        """获取文档"""
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def list_documents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None
    ) -> DocumentListResponse:
        """获取文档列表"""
        query = select(Document)
        count_query = select(func.count(Document.id))
        
        if status:
            query = query.where(Document.status == status)
            count_query = count_query.where(Document.status == status)
        
        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取列表
        query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        logger.debug(f"📋 查询文档列表: 共 {total} 条")
        
        return DocumentListResponse(
            total=total,
            items=[DocumentResponse.model_validate(doc) for doc in documents]
        )
    
    async def delete_document(self, db: AsyncSession, document_id: int) -> bool:
        """删除文档"""
        document = await self.get_document(db, document_id)
        if not document:
            return False
        
        logger.info(f"🗑️  删除文档: {document.filename}")
        
        # 删除向量数据
        await self.vectorstore_service.delete_documents(document_id)
        logger.debug(f"  - 已删除向量数据")
        
        # 删除文件
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"  - 已删除文件: {file_path}")
        
        # 删除数据库记录
        await db.delete(document)
        logger.info(f"✅ 文档删除完成: ID={document_id}")
        
        return True
    
    async def reprocess_document(
        self,
        db: AsyncSession,
        document_id: int
    ) -> Document:
        """重新处理文档"""
        logger.info(f"🔄 重新处理文档: ID={document_id}")
        
        # 先删除旧的向量数据
        await self.vectorstore_service.delete_documents(document_id)
        
        # 重新处理（会自动获取默认embedding provider）
        return await self.process_document(db, document_id)
