"""
API路由
"""
from app.routers.providers import router as providers_router
from app.routers.documents import router as documents_router
from app.routers.chatbots import router as chatbots_router
from app.routers.conversations import router as conversations_router
from app.routers.chat_logs import router as chat_logs_router
from app.routers.search_test import router as search_test_router

__all__ = [
    "providers_router",
    "documents_router", 
    "chatbots_router",
    "conversations_router",
    "chat_logs_router",
    "search_test_router"
]

