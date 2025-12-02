"""
应用配置模块
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "rag-chat"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/rag_chat.db"
    
    # 文件存储配置
    UPLOAD_DIR: Path = Path("./data/uploads")
    CHROMA_DIR: Path = Path("./data/chroma")
    
    # 文档处理配置
    # 经测试验证的最佳配置（Markdown感知分块）
    CHUNK_SIZE: int = 1000  # chunk 大小：平衡语义完整性和检索精度
    CHUNK_OVERLAP: int = 200  # chunk 重叠：20%重叠率，避免语义割裂
    
    # API密钥加密密钥 (生产环境应从环境变量读取)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()

# 确保目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

