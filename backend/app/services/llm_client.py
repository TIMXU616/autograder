"""模型调用封装：超时、两类重试、429/1305 识别、错误码映射。评分逻辑不直接碰 HTTP。"""

import json
import threading
import time

import httpx

from ..config import (
    GLM_API_KEY,
    GLM_BASE_URL,
    GLM_MODEL,
    OVERLOAD_BACKOFF,
    OVERLOAD_RETRIES,
    TIMEOUT_RETRIES,
    TIMEOUT_SECONDS,
)
from ..constants import ZHIPU_CONCURRENCY, ZHIPU_OVERLOAD
from ..errors import CreditsError, ModelUnavailableError, ModelTimeoutError

# 并发上限 1：全局信号量保证同一时刻只有一个模型请求在飞
_call_semaphore = threading.Semaphore(1)

_CREDITS_CODE = 1113  # 智谱额度不足原始码，见 docs/平台能力清单.md

# mock 模式自曝标识（P2-09）：演示若走 mock，任何拿到结果的人都要能一眼看出不是真评分
MOCK_REASON_PREFIX = "[模拟]"
MOCK_REASON_TEXT = "[模拟] 未调用模型，分数为占位值"
MOCK_WARNING = "模拟评分：未配置模型密钥，未调用 glm-4.7"
MOCK_COMMENT = "当前为模拟评分（未配置模型密钥），结果仅供联调，不代表真实评阅结论。"


class LLMClient:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key if api_key is not None else GLM_API_KEY
        self.base_url = (base_url or GLM_BASE_URL).rstrip("/")
        self.model = model or GLM_MODEL

    @property
    def is_mock(self):
        return not self.api_key

    def chat(self, system, user, temperature=0.3, max_tokens=4096) -> str:
        """返回模型输出的原始文本。无 key 时走 mock，用于骨架阶段跑通。"""
        if self.is_mock:
            return _mock_chat(user)
        return self._chat_real(system, user, temperature, max_tokens)

    def _chat_real(self, system, user, temperature, max_tokens) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking": {"type": "disabled"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/chat/completions"

        with _call_semaphore:
            return self._request_with_retry(url, headers, payload)

    def _request_with_retry(self, url, headers, payload) -> str:
        overload_attempts = 0
        retry_attempts = 0  # 超时与 5xx 共用，最多 1 次

        while True:
            try:
                resp = httpx.post(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
            except httpx.TimeoutException:
                retry_attempts += 1
                if retry_attempts <= TIMEOUT_RETRIES:
                    continue
                raise ModelTimeoutError()

            if resp.status_code == 429 or self._is_overload(resp):
                overload_attempts += 1
                if overload_attempts <= OVERLOAD_RETRIES:
                    time.sleep(OVERLOAD_BACKOFF[min(overload_attempts - 1, len(OVERLOAD_BACKOFF) - 1)])
                    continue
                raise ModelUnavailableError()

            if resp.status_code >= 500:
                retry_attempts += 1
                if retry_attempts <= TIMEOUT_RETRIES:
                    continue
                raise ModelUnavailableError()

            return self._parse_response(resp)

    @staticmethod
    def _is_overload(resp) -> bool:
        try:
            body = resp.json()
            code = body.get("error", {}).get("code") or body.get("code")
            return code in (ZHIPU_OVERLOAD, ZHIPU_CONCURRENCY)
        except Exception:
            return False

    @staticmethod
    def _parse_response(resp) -> str:
        if resp.status_code == 200:
            body = resp.json()
            return body["choices"][0]["message"]["content"]
        try:
            body = resp.json()
            code = body.get("error", {}).get("code") or body.get("code")
        except Exception:
            code = None
        if code == _CREDITS_CODE:
            raise CreditsError()
        raise ModelUnavailableError()


def _mock_chat(user: str) -> str:
    """骨架阶段占位评分：无 key 时返回合法 JSON，evidence 取自报告原文保证可检索。"""
    template_items = _extract_template_items(user)
    report_text = _extract_report_text(user)
    first_line = next((ln.strip() for ln in report_text.splitlines() if ln.strip()), "")

    items = []
    for it in template_items:
        items.append(
            {
                "item_id": it["item_id"],
                "name": it["name"],
                "max_score": it["max_score"],
                "score": round(it["max_score"] * 0.8, 1),
                "level": "good",
                "evidence": first_line[:50] if first_line else None,
                "reason": MOCK_REASON_TEXT,
                "status": "graded",
                "confidence": "medium",
                "error_code": None,
            }
        )
    total = round(sum(i["score"] for i in items), 1)
    return json.dumps(
        {
            "items": items,
            "total_score": total,
            "comment": MOCK_COMMENT,
            "highlights": [],
            "suggestions": [],
            "warnings": [MOCK_WARNING],
        },
        ensure_ascii=False,
    )


def _extract_template_items(user: str):
    marker_start = "【评分点模板】"
    marker_end = "【报告全文】"
    if marker_start not in user or marker_end not in user:
        raise ValueError("user 文本缺少【评分点模板】或【报告全文】标记")
    seg = user.split(marker_start, 1)[1].split(marker_end, 1)[0]
    start = seg.find("{")
    end = seg.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("模板 JSON 解析失败")
    data = json.loads(seg[start : end + 1])
    return data.get("items", [])


def _extract_report_text(user: str) -> str:
    marker = "【报告全文】"
    tail = user.split(marker, 1)[1]
    cut = tail.find("请按评分点逐项核查")
    if cut >= 0:
        tail = tail[:cut]
    return tail.strip()
