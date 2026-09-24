"""评分层单测：总分重算、evidence 失配降级、非法返回触发 5003。用假响应客户端打桩。"""

import json

import pytest

from app.errors import InvalidJsonError
from app.services import grader


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def chat(self, system, user, temperature=0.3, max_tokens=4096):
        r = self.responses[self.calls % len(self.responses)]
        self.calls += 1
        return r


TEMPLATE = {
    "template_id": "tpl-test",
    "name": "测试模板",
    "course": "数据结构",
    "total_score": 20,
    "items": [
        {"item_id": 1, "name": "实验目的与原理", "max_score": 10},
        {"item_id": 2, "name": "代码实现", "max_score": 10},
    ],
}

REPORT = "实验目的：掌握单链表的基本操作。实验原理：单链表由节点构成，每个节点包含数据域和指针域。代码实现见附录。"


def _item(item_id, name, max_score, score, evidence):
    return {
        "item_id": item_id,
        "name": name,
        "max_score": max_score,
        "score": score,
        "level": "good",
        "evidence": evidence,
        "reason": "测试",
        "status": "graded",
        "confidence": "high",
        "error_code": None,
    }


def test_total_recalc():
    resp = json.dumps(
        {
            "items": [
                _item(1, "实验目的与原理", 10, 10.0, "掌握单链表的基本操作"),
                _item(2, "代码实现", 10, 0.0, None),
            ],
            "total_score": 99.0,  # 故意与各项之和不等
            "warnings": [],
        },
        ensure_ascii=False,
    )
    client = FakeClient([resp])
    result = grader.grade_report(TEMPLATE, REPORT, llm_client=client)
    assert result["total_score"] == 10.0
    assert any("重算" in w for w in result["warnings"])


def test_evidence_mismatch():
    resp = json.dumps(
        {
            "items": [
                _item(1, "实验目的与原理", 10, 8.0, "这段文字不在原文里"),
                _item(2, "代码实现", 10, 5.0, "单链表由节点构成"),
            ],
            "total_score": 13.0,
            "warnings": [],
        },
        ensure_ascii=False,
    )
    client = FakeClient([resp])
    result = grader.grade_report(TEMPLATE, REPORT, llm_client=client)
    assert result["items"][0]["status"] == "low_confidence"
    assert result["items"][0]["confidence"] == "low"
    assert result["items"][0]["error_code"] is None
    assert result["items"][0]["score"] == 8.0  # 保留原得分
    assert any("未能" in w for w in result["warnings"])


def test_invalid_json():
    client = FakeClient(["not a json", "still not a json"])
    with pytest.raises(InvalidJsonError):
        grader.grade_report(TEMPLATE, REPORT, llm_client=client)


def test_offtopic_guard():
    """跑题兜底：warnings 含跑题关键词时，即使模型给了非零分也强制清零。"""
    resp = json.dumps(
        {
            "items": [
                _item(1, "实验目的与原理", 10, 8.0, "掌握单链表的基本操作"),
                _item(2, "代码实现", 10, 5.0, "单链表由节点构成"),
            ],
            "total_score": 13.0,
            "warnings": ["报告内容与数据结构实验无关，各项均 0 分"],
        },
        ensure_ascii=False,
    )
    client = FakeClient([resp])
    result = grader.grade_report(TEMPLATE, REPORT, llm_client=client)
    assert result["total_score"] == 0.0
    for it in result["items"]:
        assert it["score"] == 0.0
        assert it["level"] == "absent"
        assert it["status"] == "graded"
        assert it["confidence"] == "high"
        assert it["evidence"] is None
    assert any("报告内容与数据结构实验无关" in w for w in result["warnings"])
    assert not any("重算" in w for w in result["warnings"]), "跑题兜底不应追加总分重算噪音"


def test_offtopic_by_domain_terms():
    """主判据：正文不含任何数据结构术语即判跑题并清零，不依赖 warnings 措辞。"""
    resp = json.dumps(
        {
            "items": [
                _item(1, "实验目的与原理", 10, 5.7, None),
                _item(2, "代码实现", 10, 7.5, None),
            ],
            "total_score": 13.2,
            "warnings": [
                "报告缺少实验目的与原理相关内容",
                "报告缺少实验环境与步骤相关内容",
            ],
        },
        ensure_ascii=False,
    )
    client = FakeClient([resp])
    offtopic_report = (
        "本报告是关于校园食堂消费情况的调研。我们通过问卷回收了 100 份有效问卷，"
        "统计了同学们每周的消费金额分布，并给出了改进建议。"
    )
    result = grader.grade_report(TEMPLATE, offtopic_report, llm_client=client)
    assert result["total_score"] == 0.0
    for it in result["items"]:
        assert it["score"] == 0.0
        assert it["level"] == "absent"
    assert any("报告内容与数据结构实验无关" in w for w in result["warnings"])


def test_code_only_not_offtopic():
    """反例：正文只有代码但含领域术语，不得误判跑题。"""
    resp = json.dumps(
        {
            "items": [
                _item(1, "实验目的与原理", 10, 0.0, None),
                _item(2, "代码实现", 10, 8.0, "void insert(Node* head)"),
            ],
            "total_score": 8.0,
            "warnings": [],
        },
        ensure_ascii=False,
    )
    client = FakeClient([resp])
    code_report = (
        "struct Node { int data; struct Node* next; };\n"
        "void insert(Node* head, int val) {}\n"
        "void sort_list(Node* head) {}\n"
        "void traverse_tree(Node* root) {}"
    )
    result = grader.grade_report(TEMPLATE, code_report, llm_client=client)
    assert result["total_score"] == 8.0  # 未被清零
    assert not any("报告内容与数据结构实验无关" in w for w in result["warnings"])


def test_mock_mode_self_exposes():
    """mock 模式必须自曝：[模拟] 前缀、固定警示串只出现一次、comment 含模拟字样。"""
    from app.services.llm_client import (
        LLMClient,
        MOCK_REASON_PREFIX,
        MOCK_WARNING,
    )

    client = LLMClient(api_key="")  # 空 key 强制走 mock
    assert client.is_mock

    result = grader.grade_report(TEMPLATE, REPORT, llm_client=client)
    for it in result["items"]:
        assert str(it["reason"]).startswith(MOCK_REASON_PREFIX)
    assert result["warnings"].count(MOCK_WARNING) == 1
    assert "模拟" in (result["comment"] or "")
