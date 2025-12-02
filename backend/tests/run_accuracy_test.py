"""
RAG 系统准确性测试

使用方法:
    # 运行检索测试
    python tests/run_accuracy_test.py --mode retrieval
    
    # 运行完整测试（检索+答案质量）
    python tests/run_accuracy_test.py --mode full
    
    # 指定输出目录
    python tests/run_accuracy_test.py --output-dir ./test_results
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import async_session_maker
from app.services.chat_service import ChatService
from app.services.vectorstore_service import VectorStoreService
from app.models import Chatbot, EmbeddingProvider, Conversation
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from metrics import RetrievalMetrics, AnswerQualityMetrics


def load_test_cases():
    """加载测试用例"""
    test_file = Path(__file__).parent / "test_data" / "qa_test_set.json"
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)["test_cases"]


async def run_retrieval_test(test_cases, vectorstore_service, embedding_provider):
    """运行检索质量测试（基于内容关键词匹配）"""
    print("\n" + "=" * 60)
    print("📊 检索质量测试")
    print("=" * 60)
    
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {case['question']}")
        
        try:
            docs_with_scores = await vectorstore_service.similarity_search_with_score(
                embedding_provider=embedding_provider,
                query=case["question"],
                k=10
            )
            
            # 获取检索到的文档内容
            retrieved_contents = [doc.page_content for doc, _ in docs_with_scores[:5]]
            combined_content = "\n".join(retrieved_contents).lower()
            
            # 检查关键词是否出现在检索结果中
            retrieval_keywords = case.get("retrieval_keywords", case.get("expected_keywords", []))
            keywords_found = sum(1 for kw in retrieval_keywords if kw.lower() in combined_content)
            keyword_coverage = keywords_found / len(retrieval_keywords) if retrieval_keywords else 0
            
            # 计算相似度分数统计
            top_scores = [float(score) for _, score in docs_with_scores[:5]]
            avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
            
            result = {
                "question": case["question"],
                "category": case.get("category", "unknown"),
                "difficulty": case.get("difficulty", "medium"),
                "keyword_coverage": keyword_coverage,
                "keywords_found": keywords_found,
                "keywords_total": len(retrieval_keywords),
                "avg_similarity": avg_score,
                "top_scores": top_scores[:3],
                "preview": retrieved_contents[0][:100] if retrieved_contents else ""
            }
            results.append(result)
            
            status = "✓" if keyword_coverage >= 0.6 else "⚠"
            print(f"  {status} 关键词覆盖: {keywords_found}/{len(retrieval_keywords)} ({keyword_coverage:.1%})")
            print(f"    平均相似度: {avg_score:.3f}")
            
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            results.append({"question": case["question"], "error": str(e)})
    
    return _summarize_retrieval(results)


async def run_answer_test(test_cases, chat_service, chatbot, db):
    """运行答案质量测试"""
    print("\n" + "=" * 60)
    print("📝 答案质量测试")
    print("=" * 60)
    
    metrics = AnswerQualityMetrics()
    results = []
    
    # 创建测试会话
    conversation = Conversation(chatbot_id=chatbot.id, title="测试会话")
    db.add(conversation)
    await db.commit()
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation.id)
        .options(selectinload(Conversation.chatbot), selectinload(Conversation.messages))
    )
    conversation = result.scalar_one()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {case['question']}")
        
        try:
            answer, _ = await chat_service.chat(
                db=db, conversation=conversation, user_message=case["question"], stream=False
            )
            
            result = {
                "question": case["question"],
                "answer": answer,
                "category": case["category"],
                "difficulty": case["difficulty"],
                "keyword_coverage": metrics.keyword_coverage(answer, case["expected_keywords"]),
                "length_score": metrics.answer_length_score(answer, 20, 500),
                "no_hallucination": metrics.no_hallucination_keywords(
                    answer, ["抱歉", "不知道", "无法回答", "没有相关信息"]
                )
            }
            results.append(result)
            
            print(f"  关键词覆盖: {result['keyword_coverage']:.3f}")
            print(f"  答案预览: {answer[:80]}...")
            
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            results.append({"question": case["question"], "error": str(e)})
    
    return _summarize_answer(results)


def _summarize_retrieval(results):
    """汇总检索测试结果"""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"error": "无有效结果"}
    
    avg_coverage = sum(r["keyword_coverage"] for r in valid) / len(valid)
    avg_similarity = sum(r["avg_similarity"] for r in valid) / len(valid)
    full_coverage_count = sum(1 for r in valid if r["keyword_coverage"] == 1.0)
    
    summary = {
        "avg_keyword_coverage": avg_coverage,
        "avg_similarity": avg_similarity,
        "full_coverage_rate": full_coverage_count / len(valid),
        "total": len(results),
        "successful": len(valid)
    }
    
    # 评估质量
    if avg_coverage >= 0.8:
        quality = "优秀 🎉"
    elif avg_coverage >= 0.6:
        quality = "良好 ✓"
    else:
        quality = "需要改进 ⚠️"
    
    print("\n" + "-" * 60)
    print(f"平均关键词覆盖: {avg_coverage:.1%}")
    print(f"完全覆盖率: {full_coverage_count}/{len(valid)} ({summary['full_coverage_rate']:.1%})")
    print(f"平均相似度: {avg_similarity:.3f}")
    print(f"整体质量: {quality}")
    print(f"成功: {summary['successful']}/{summary['total']}")
    
    return {"summary": summary, "quality": quality, "details": results}


def _summarize_answer(results):
    """汇总答案测试结果"""
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"error": "无有效结果"}
    
    summary = {
        "avg_keyword_coverage": sum(r["keyword_coverage"] for r in valid) / len(valid),
        "avg_length_score": sum(r["length_score"] for r in valid) / len(valid),
        "hallucination_free_rate": sum(1 for r in valid if r["no_hallucination"]) / len(valid),
        "total": len(results),
        "successful": len(valid)
    }
    
    print("\n" + "-" * 60)
    print(f"平均关键词覆盖: {summary['avg_keyword_coverage']:.3f}")
    print(f"无幻觉率: {summary['hallucination_free_rate']:.3f}")
    print(f"成功: {summary['successful']}/{summary['total']}")
    
    return {"summary": summary, "details": results}


async def run_tests(mode: str, output_dir: str):
    """运行测试"""
    print("=" * 60)
    print(f"🎯 RAG 系统准确性测试 (模式: {mode})")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    test_cases = load_test_cases()
    print(f"加载了 {len(test_cases)} 个测试用例")
    
    # 获取配置
    async with async_session_maker() as db:
        result = await db.execute(
            select(EmbeddingProvider).where(EmbeddingProvider.is_default == True)
        )
        embedding_provider = result.scalar_one_or_none()
        
        if not embedding_provider:
            print("❌ 未找到默认嵌入提供商")
            return
        
        result = await db.execute(select(Chatbot).limit(1))
        chatbot = result.scalar_one_or_none()
        
        print(f"嵌入模型: {embedding_provider.name} ({embedding_provider.model})")
        await db.refresh(embedding_provider)
        if chatbot:
            await db.refresh(chatbot)
    
    report = {"test_time": datetime.now().isoformat(), "mode": mode}
    
    # 运行检索测试
    vectorstore_service = VectorStoreService()
    report["retrieval"] = await run_retrieval_test(
        test_cases, vectorstore_service, embedding_provider
    )
    
    # 运行答案测试（仅 full 模式）
    if mode == "full" and chatbot:
        chat_service = ChatService()
        async with async_session_maker() as db:
            result = await db.execute(
                select(Chatbot)
                .where(Chatbot.id == chatbot.id)
                .options(selectinload(Chatbot.llm_provider), selectinload(Chatbot.embedding_provider))
            )
            chatbot_session = result.scalar_one()
            report["answer"] = await run_answer_test(
                test_cases, chat_service, chatbot_session, db
            )
    
    # 保存报告
    report_path = output_path / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ 测试完成！报告: {report_path}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="RAG 系统准确性测试")
    parser.add_argument("--mode", choices=["retrieval", "full"], default="retrieval",
                        help="测试模式: retrieval(仅检索) 或 full(完整)")
    parser.add_argument("--output-dir", default="./test_results", help="输出目录")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_tests(args.mode, args.output_dir))
    except KeyboardInterrupt:
        print("\n⚠️ 测试中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
