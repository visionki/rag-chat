#!/usr/bin/env python3
"""
向量库管理工具

用于清空、重建、查看向量库状态
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.vectorstore_service import VectorStoreService
from app.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("vectorstore-manager")


def reset_vectorstore():
    """清空并重建向量库"""
    logger.info("=" * 80)
    logger.info("⚠️  即将清空向量库，所有向量数据将被删除！")
    logger.info("=" * 80)
    
    confirm = input("确认要继续吗？(输入 'yes' 确认): ").strip().lower()
    
    if confirm != "yes":
        logger.info("❌ 操作已取消")
        return
    
    logger.info("🗑️  正在清空向量库...")
    
    vs_service = VectorStoreService()
    vs_service.reset_collection()
    
    logger.info("✅ 向量库已清空并重建")
    logger.info("💡 提示：请重新上传文档以重建向量索引")


def show_stats():
    """显示向量库统计信息"""
    vs_service = VectorStoreService()
    stats = vs_service.get_collection_stats()
    
    logger.info("=" * 80)
    logger.info("📊 向量库统计信息")
    logger.info("=" * 80)
    logger.info(f"Collection名称: {stats['collection_name']}")
    logger.info(f"向量总数: {stats['total_vectors']}")
    
    # 获取collection详细信息
    collection = vs_service.get_or_create_collection()
    metadata = collection.metadata
    
    logger.info("\nCollection配置:")
    for key, value in metadata.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("=" * 80)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("向量库管理工具")
        print("\n用法:")
        print("  python manage_vectorstore.py stats    # 查看统计信息")
        print("  python manage_vectorstore.py reset    # 清空并重建向量库")
        return
    
    command = sys.argv[1]
    
    if command == "stats":
        show_stats()
    elif command == "reset":
        reset_vectorstore()
    else:
        logger.error(f"❌ 未知命令: {command}")
        logger.info("可用命令: stats, reset")


if __name__ == "__main__":
    main()


