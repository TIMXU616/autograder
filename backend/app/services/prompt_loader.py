"""提示词加载与校验：靠三个机器可读标记定位，缺失即抛错，禁止静默降级。"""

import json
import re
from pathlib import Path

PARAMS_TAG = "<!-- PARAMS -->"
SYSTEM_TAG = "<!-- SYSTEM -->"
USER_TAG = "<!-- USER -->"

_TAGS = [PARAMS_TAG, SYSTEM_TAG, USER_TAG]


def load_prompt(path) -> dict:
    """读取提示词文件，返回 {params, system, user}。"""
    content = Path(path).read_text(encoding="utf-8")

    for tag in _TAGS:
        count = content.count(tag)
        if count != 1:
            raise ValueError(
                f"提示词文件缺少或重复标记 {tag}（出现 {count} 次），请检查 {path}"
            )

    params = _extract_params(content)
    system = _extract_between(content, SYSTEM_TAG, USER_TAG)
    user = content.split(USER_TAG, 1)[1].strip()

    if "{template_json}" not in user or "{report_text}" not in user:
        raise ValueError("user 模板缺少 {template_json} 或 {report_text} 占位符")

    return {"params": params, "system": system, "user": user}


def _extract_params(content: str) -> dict:
    after = content.split(PARAMS_TAG, 1)[1]
    m = re.search(r"```json\s*\n(.*?)```", after, re.DOTALL)
    if not m:
        raise ValueError("PARAMS 标记后缺少 json 代码块")
    return json.loads(m.group(1))


def _extract_between(content: str, start_tag: str, end_tag: str) -> str:
    _, after = content.split(start_tag, 1)
    before, _ = after.split(end_tag, 1)
    return before.strip()
