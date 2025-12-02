"""
RAG 系统评估指标

包含检索质量和答案质量的评估指标计算。
"""
from typing import List
import re
import numpy as np


class RetrievalMetrics:
    """检索质量评估指标"""
    
    @staticmethod
    def precision_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
        """计算 Precision@K"""
        if k == 0 or len(retrieved_docs) == 0:
            return 0.0
        retrieved_k = retrieved_docs[:k]
        relevant_retrieved = sum(1 for doc in retrieved_k if doc in relevant_docs)
        return relevant_retrieved / min(k, len(retrieved_k))
    
    @staticmethod
    def recall_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
        """计算 Recall@K"""
        if len(relevant_docs) == 0:
            return 0.0
        retrieved_k = retrieved_docs[:k]
        relevant_retrieved = sum(1 for doc in retrieved_k if doc in relevant_docs)
        return relevant_retrieved / len(relevant_docs)
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
        """计算 MRR (Mean Reciprocal Rank)"""
        for i, doc in enumerate(retrieved_docs, 1):
            if doc in relevant_docs:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved_docs: List[str], relevant_docs: List[str], k: int) -> float:
        """计算 NDCG@K (Normalized Discounted Cumulative Gain)"""
        def dcg(relevances: List[int]) -> float:
            return sum(rel / np.log2(i + 2) for i, rel in enumerate(relevances))
        
        retrieved_k = retrieved_docs[:k]
        relevances = [1 if doc in relevant_docs else 0 for doc in retrieved_k]
        actual_dcg = dcg(relevances)
        
        ideal_relevances = [1] * min(len(relevant_docs), k) + [0] * max(0, k - len(relevant_docs))
        ideal_dcg = dcg(ideal_relevances)
        
        return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


class AnswerQualityMetrics:
    """答案质量评估指标"""
    
    @staticmethod
    def keyword_coverage(answer: str, expected_keywords: List[str]) -> float:
        """计算关键词覆盖率"""
        if not expected_keywords:
            return 1.0
        answer_lower = answer.lower()
        matched = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
        return matched / len(expected_keywords)
    
    @staticmethod
    def answer_length_score(answer: str, min_length: int = 10, max_length: int = 500) -> float:
        """评估答案长度是否合适"""
        length = len(answer.strip())
        if length < min_length:
            return length / min_length
        elif length > max_length:
            return max(0, 1 - (length - max_length) / max_length)
        return 1.0
    
    @staticmethod
    def no_hallucination_keywords(answer: str, forbidden_keywords: List[str]) -> bool:
        """检查答案是否包含幻觉关键词"""
        answer_lower = answer.lower()
        return not any(kw.lower() in answer_lower for kw in forbidden_keywords)
    
    @staticmethod
    def contains_expected_info(answer: str, expected_patterns: List[str]) -> float:
        """检查答案是否包含期望的信息模式"""
        if not expected_patterns:
            return 1.0
        matched = sum(1 for pattern in expected_patterns if re.search(pattern, answer, re.IGNORECASE))
        return matched / len(expected_patterns)

