"""
日志配置模块
"""
import sys
import logging
from datetime import datetime
from pathlib import Path
from app.config import settings

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 颜色代码 (用于控制台彩色输出)
COLORS = {
    "DEBUG": "\033[36m",     # 青色
    "INFO": "\033[32m",      # 绿色
    "WARNING": "\033[33m",   # 黄色
    "ERROR": "\033[31m",     # 红色
    "CRITICAL": "\033[35m",  # 紫色
    "RESET": "\033[0m",      # 重置
}


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    def format(self, record):
        # 添加颜色
        color = COLORS.get(record.levelname, COLORS["RESET"])
        record.levelname = f"{color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logging():
    """配置日志系统"""
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # 清除已有处理器
    root_logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(ColoredFormatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)
    
    # 设置第三方库日志级别（减少噪音）
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)


# 预定义的日志器
logger = get_logger("rag-chat")


