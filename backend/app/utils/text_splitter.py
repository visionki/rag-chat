"""
文本分块器
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownTextSplitter
from app.config import settings


def get_text_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    is_markdown: bool = False
) -> RecursiveCharacterTextSplitter:
    """
    获取文本分块器
    
    Args:
        chunk_size: 块大小
        chunk_overlap: 块重叠
        is_markdown: 是否为 Markdown 格式
    """
    size = chunk_size or settings.CHUNK_SIZE
    overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    if is_markdown:
        # Markdown 感知分块 - 优先按标题和段落切分
        return RecursiveCharacterTextSplitter(
            chunk_size=size,
            chunk_overlap=overlap,
            length_function=len,
            separators=[
                # Markdown 标题（按优先级从高到低）
                "\n## ",      # 二级标题
                "\n### ",     # 三级标题
                "\n#### ",    # 四级标题
                "\n\n",       # 段落
                "\n",         # 换行
                "。",         # 中文句号
                ".",          # 英文句号
                " ",          # 空格
                ""            # 字符
            ]
        )
    
    # 通用分块器
    return RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        separators=[
            "\n\n",       # 段落
            "\n",         # 换行
            "。",         # 中文句号
            ".",          # 英文句号
            " ",          # 空格
            ""            # 字符
        ]
    )


def get_markdown_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None
) -> MarkdownTextSplitter:
    """
    获取 Markdown 专用分块器
    会保留章节结构
    """
    return MarkdownTextSplitter(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP
    )

