"""评分层：填模板、调模型、解析 JSON、总分重算、evidence 校验降级。"""

import json
import logging
import re
from pathlib import Path

from ..errors import InvalidJsonError
from .llm_client import LLMClient, MOCK_REASON_PREFIX, MOCK_WARNING
from .prompt_loader import load_prompt

logger = logging.getLogger(__name__)

DEFAULT_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "scoring_v1.md"

# 跑题判定关键词（次判据）：warnings 任意一条命中即判定为跑题
OFFTOPIC_KEYWORDS = ("无关", "跑题", "不是数据结构")

# 数据结构术语（主判据）：正文里一个都不出现即判定跑题，不依赖模型措辞
DOMAIN_TERMS_CN = (
    "链表", "线性表", "顺序表", "数组", "栈", "队列", "树", "二叉树", "图", "邻接",
    "排序", "查找", "哈希", "散列", "堆", "递归", "迭代", "指针", "节点", "结点",
    "遍历", "插入", "删除", "时间复杂度", "空间复杂度", "算法", "数据结构", "实验报告",
)
DOMAIN_TERMS_EN = (
    "linked", "list", "stack", "queue", "tree", "graph", "sort", "search", "hash",
    "heap", "insert", "delete", "traverse", "node", "pointer", "o(",
)


def _has_domain_terms(report_text: str, terms=None) -> bool:
    """正文里出现任一课程领域术语即认为与课程相关。

    terms 为模板自带的 domain_terms（{"cn": [...], "en": [...]}）；
    模板没给该字段时回退内置数据结构表，保证 tpl-1001 行为不变。
    """
    cn = (terms or {}).get("cn") or DOMAIN_TERMS_CN
    en = (terms or {}).get("en") or DOMAIN_TERMS_EN
    if any(t in report_text for t in cn):
        return True
    lower = report_text.lower()
    return any(t in lower for t in en)


def _is_offtopic(report_text: str, warnings: list, terms=None):
    """两级判据。返回 (是否跑题, 命中原因)。主判据确定性，不依赖模型措辞。"""
    if not _has_domain_terms(report_text, terms):
        return True, "正文不含任何课程领域术语"
    if any(k in w for w in warnings for k in OFFTOPIC_KEYWORDS):
        return True, "warnings 命中跑题关键词"
    return False, None


OFFTOPIC_FIXED_WARNING = "报告内容与数据结构实验无关"  # 契约固定串（course 为数据结构时即为此串）


def _offtopic_warning(course=None) -> str:
    """跑题固定警示串按模板课程生成；无 course 时回退契约固定串，保证 tpl-1001 行为不变。"""
    if course:
        return f"报告内容与{course}实验无关"
    return OFFTOPIC_FIXED_WARNING


def grade_report(template: dict, report_text: str, prompt_path=None, llm_client=None) -> dict:
    """对一份报告评分，返回 {items, total_score, warnings}。"""
    path = prompt_path or DEFAULT_PROMPT_PATH
    prompt = load_prompt(path)

    user = prompt["user"].replace(
        "{template_json}", json.dumps(template, ensure_ascii=False)
    ).replace("{report_text}", report_text)

    client = llm_client or LLMClient()
    params = prompt["params"]

    raw = client.chat(
        prompt["system"],
        user,
        temperature=params.get("temperature", 0.3),
        max_tokens=params.get("max_tokens", 4096),
    )

    data = _parse_json(raw)
    # 非法 JSON 重试 1 次
    if data is None:
        raw = client.chat(
            prompt["system"],
            user,
            temperature=params.get("temperature", 0.3),
            max_tokens=params.get("max_tokens", 4096),
        )
        data = _parse_json(raw)
        if data is None:
            raise InvalidJsonError()

    return _normalize(
        data, report_text, template.get("domain_terms"), template.get("course")
    )


def _parse_json(raw: str):
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def _normalize(data: dict, report_text: str, domain_terms=None, course=None) -> dict:
    items = data.get("items", [])
    warnings = list(data.get("warnings", []) or [])
    comment = data.get("comment") or ""
    highlights = list(data.get("highlights", []) or [])
    suggestions = list(data.get("suggestions", []) or [])

    # 顶层只保留六个键，其他键忽略并记日志
    allowed = {"items", "total_score", "comment", "highlights", "suggestions", "warnings"}
    extra = set(data.keys()) - allowed
    if extra:
        logger.warning("模型返回了未预期的顶层键，已忽略: %s", sorted(extra))

    # score 归一化为 1 位小数，None 保持 None
    for item in items:
        if item.get("score") is not None:
            item["score"] = round(float(item["score"]), 1)

    # evidence 归一化子串匹配，失配降级
    norm_report = _normalize_ws(report_text)
    for item in items:
        ev = item.get("evidence")
        if ev and _normalize_ws(ev) not in norm_report:
            item["status"] = "low_confidence"
            item["confidence"] = "low"
            item["error_code"] = None
            warnings.append(f"第 {item.get('item_id')} 项依据未能在原文中定位")

    # 跑题兜底：主判据看正文术语（确定性，不依赖模型措辞），次判据看模型 warnings，任一命中即清零
    offtopic_hit, offtopic_reason = _is_offtopic(report_text, warnings, domain_terms)
    if offtopic_hit:
        for item in items:
            item["score"] = 0.0
            item["level"] = "absent"
            item["status"] = "graded"
            item["confidence"] = "high"
            item["evidence"] = None
        warn = _offtopic_warning(course)
        if warn not in warnings:
            warnings.append(warn)
        logger.warning("跑题兜底触发（%s），全部评分项已强制清零", offtopic_reason)

    # total_score 与各项之和不等，以各项之和为准重算
    # 跑题兜底引起的是后端改写分数后的差异，不是模型输出不一致，不追加这条噪音
    s = round(sum(i.get("score") or 0.0 for i in items), 1)
    if not offtopic_hit and abs(float(data.get("total_score") or 0.0) - s) > 0.01:
        warnings.append("total_score 与各项之和不等，已按各项之和重算")

    # mock 自曝（P2-09）：有模拟项时，保证固定警示串存在且只出现一次；真模型路径不受影响
    if any(str(it.get("reason") or "").startswith(MOCK_REASON_PREFIX) for it in items):
        warnings = [w for w in warnings if w != MOCK_WARNING]
        warnings.insert(0, MOCK_WARNING)

    return {
        "items": items,
        "total_score": s,
        "comment": comment,
        "highlights": highlights,
        "suggestions": suggestions,
        "warnings": warnings,
    }


def _normalize_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)
