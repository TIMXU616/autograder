"""第二套模板接入单测：换模板换判据、跑题术语随模板、种子支持多文件与坏文件容错。"""

import json
import sys
from pathlib import Path

from app.services import grader

BACKEND = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BACKEND.parent / "templates" / "grading"

TPL_1001 = json.loads((TEMPLATE_DIR / "数据结构实验报告.json").read_text(encoding="utf-8"))
TPL_1002 = json.loads((TEMPLATE_DIR / "计算机网络实验报告评分模板.json").read_text(encoding="utf-8"))

# 网络报告正文：含 TCP 术语、刻意不含任何数据结构术语（「节点」是数据结构术语，故用「主机」）
NETWORK_REPORT = (
    "一、实验目的\n"
    "本实验使用 NS-3 仿真 TCP 拥塞控制，观察慢启动与拥塞避免阶段的窗口变化，"
    "测量不同带宽与时延下的吞吐量、丢包率与 RTT。\n"
    "二、实验环境\n"
    "Ubuntu 22.04 与 ns-3.35，配置链路带宽 10Mbps、时延 20ms。\n"
    "三、实验方案\n"
    "两台主机经一条链路相连，运行 socket 程序发送数据流并抓包。"
)


class CapturingClient:
    """记录送入模型的 user 文本，用于断言判据文案随模板走。"""

    def __init__(self, response):
        self.response = response
        self.users = []

    def chat(self, system, user, temperature=0.3, max_tokens=4096):
        self.users.append(user)
        return self.response


def _template_segment(user: str) -> str:
    """取 user 里【评分点模板】与【报告全文】之间的模板 JSON 段，排除报告正文干扰。"""
    return user.split("【评分点模板】", 1)[1].split("【报告全文】", 1)[0]


def _fake_response(total=8.0):
    return json.dumps(
        {
            "items": [
                {
                    "item_id": 1,
                    "name": "任意",
                    "max_score": 10,
                    "score": 8.0,
                    "level": "good",
                    "evidence": None,
                    "reason": "占位",
                    "status": "graded",
                    "confidence": "medium",
                    "error_code": None,
                }
            ],
            "total_score": total,
            "comment": "占位",
            "highlights": [],
            "suggestions": [],
            "warnings": [],
        },
        ensure_ascii=False,
    )


def test_two_templates_items_differ():
    """两套模板的评分项名称与分值分布都不同，满分和均为 100。"""
    names1 = [it["name"] for it in TPL_1001["items"]]
    names2 = [it["name"] for it in TPL_1002["items"]]
    scores1 = [it["max_score"] for it in TPL_1001["items"]]
    scores2 = [it["max_score"] for it in TPL_1002["items"]]

    assert names1 != names2, "两套模板的评分项名称必须不同"
    assert scores1 != scores2, "两套模板的分值分布必须不同"
    assert sum(scores1) == 100 and sum(scores2) == 100


def test_prompt_text_follows_template():
    """送入模型的 user 文本里出现各自模板的判据文案。"""
    c1 = CapturingClient(_fake_response())
    grader.grade_report(TPL_1001, NETWORK_REPORT, llm_client=c1)
    c2 = CapturingClient(_fake_response())
    grader.grade_report(TPL_1002, NETWORK_REPORT, llm_client=c2)

    seg1 = _template_segment(c1.users[0])
    seg2 = _template_segment(c2.users[0])
    assert "链表" in seg1 and "拥塞控制" not in seg1
    assert "拥塞控制" in seg2 and "链表" not in seg2


def test_offtopic_follows_template_domain_terms():
    """同一份网络正文：配 tpl-1002 不跑题，配 tpl-1001 跑题并清零。本次最重要的回归保护。"""
    resp = _fake_response()  # 单项 8.0，与 total 一致，避免被重算逻辑改写

    r2 = grader.grade_report(TPL_1002, NETWORK_REPORT, llm_client=CapturingClient(resp))
    assert r2["total_score"] == 8.0, "网络模板不得把网络报告判为跑题"
    assert not any("无关" in w for w in r2["warnings"])

    r1 = grader.grade_report(TPL_1001, NETWORK_REPORT, llm_client=CapturingClient(resp))
    assert r1["total_score"] == 0.0, "数据结构模板下该正文应被判跑题并清零"


def test_seed_reads_multiple_templates(tmp_db, tmp_path):
    """种子遍历目录下所有模板；坏文件只跳过该文件，不影响其余。"""
    sys.path.insert(0, str(BACKEND / "scripts"))
    from seed import seed_templates

    from app.repositories import grading_repo

    d = tmp_path / "tpl"
    d.mkdir()
    (d / "a.json").write_text(json.dumps(TPL_1001, ensure_ascii=False), encoding="utf-8")
    (d / "b.json").write_text(json.dumps(TPL_1002, ensure_ascii=False), encoding="utf-8")
    (d / "bad.json").write_text("{ 这不是合法 JSON", encoding="utf-8")

    seed_templates(d)

    lst = grading_repo.list_templates()
    assert lst["total"] == 2, "两个合法模板都应导入，坏文件只跳过自己"
    ids = {it["template_id"] for it in lst["items"]}
    assert ids == {"tpl-1001", "tpl-1002"}
