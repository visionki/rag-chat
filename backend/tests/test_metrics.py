"""
指标计算单元测试
"""
import pytest
import sys
from pathlib import Path

# 添加 tests 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from metrics import RetrievalMetrics, AnswerQualityMetrics


class TestRetrievalMetrics:
    """检索指标测试"""
    
    @pytest.fixture
    def metrics(self):
        return RetrievalMetrics()
    
    def test_precision_at_k(self, metrics):
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3", "doc5"]
        
        assert metrics.precision_at_k(retrieved, relevant, 3) == pytest.approx(2/3)
        assert metrics.precision_at_k(retrieved, relevant, 5) == pytest.approx(3/5)
        assert metrics.precision_at_k([], relevant, 5) == 0.0
    
    def test_recall_at_k(self, metrics):
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3", "doc5"]
        
        assert metrics.recall_at_k(retrieved, relevant, 3) == pytest.approx(2/3)
        assert metrics.recall_at_k(retrieved, relevant, 5) == 1.0
        assert metrics.recall_at_k(retrieved, [], 5) == 0.0
    
    def test_mrr(self, metrics):
        # 第一个相关文档在第2位
        assert metrics.mean_reciprocal_rank(["x", "doc1", "doc2"], ["doc1"]) == 0.5
        # 第一个相关文档在第1位
        assert metrics.mean_reciprocal_rank(["doc1", "doc2"], ["doc1"]) == 1.0
        # 没有相关文档
        assert metrics.mean_reciprocal_rank(["x", "y", "z"], ["doc1"]) == 0.0
    
    def test_ndcg_at_k(self, metrics):
        # 完美排序
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc2", "doc3"]
        assert metrics.ndcg_at_k(retrieved, relevant, 5) == pytest.approx(1.0)
        
        # 部分相关
        retrieved = ["doc1", "x", "doc2", "y", "doc3"]
        assert 0 < metrics.ndcg_at_k(retrieved, relevant, 5) < 1


class TestAnswerQualityMetrics:
    """答案质量指标测试"""
    
    @pytest.fixture
    def metrics(self):
        return AnswerQualityMetrics()
    
    def test_keyword_coverage(self, metrics):
        answer = "Claude 4.5 包含 Opus 4.5、Sonnet 4.5 和 Haiku 4.5"
        keywords = ["Opus 4.5", "Sonnet 4.5", "Haiku 4.5"]
        
        assert metrics.keyword_coverage(answer, keywords) == 1.0
        assert metrics.keyword_coverage("只有 Opus 4.5", keywords) == pytest.approx(1/3)
        assert metrics.keyword_coverage(answer, []) == 1.0
    
    def test_answer_length_score(self, metrics):
        assert metrics.answer_length_score("合适长度" * 10, 10, 200) == 1.0
        assert metrics.answer_length_score("短", 10, 200) < 1.0
        assert metrics.answer_length_score("很长" * 200, 10, 200) < 1.0
    
    def test_no_hallucination(self, metrics):
        forbidden = ["抱歉", "不知道"]
        
        assert metrics.no_hallucination_keywords("正常答案", forbidden) == True
        assert metrics.no_hallucination_keywords("抱歉，我不知道", forbidden) == False
    
    def test_contains_expected_info(self, metrics):
        answer = "定价为 $3/MTok 输入，$15/MTok 输出"
        patterns = [r"\$3", r"\$15"]
        
        assert metrics.contains_expected_info(answer, patterns) == 1.0
        assert metrics.contains_expected_info("无关答案", patterns) == 0.0

