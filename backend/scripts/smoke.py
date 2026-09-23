"""冒烟脚本：拉模板 → 上传 docx → 触发评阅 → 轮询到终态 → 拉成绩列表。

用法：先启动服务，再执行
    uvicorn app.main:app --reload
    python scripts/smoke.py [报告文件路径]
每步打印返回码与关键字段，最后打印一行 PASS 或 FAIL。
"""

import sys
import tempfile
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
TERMINAL = ("success", "partial_success", "failed")
DEFAULT_DOCX = (
    Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "case_good.docx"
)


def _make_unique_docx(src: Path) -> Path:
    """基于样例生成内容唯一的临时 docx，避免命中上传幂等键（4091）。"""
    from docx import Document

    doc = Document(str(src))
    stamp = int(time.time() * 1000)
    doc.add_paragraph(f"冒烟测试标记 {stamp}")
    tmp = Path(tempfile.gettempdir()) / f"smoke_{stamp}.docx"
    doc.save(str(tmp))
    return tmp


def main():
    docx = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DOCX)
    if docx.exists():
        docx = _make_unique_docx(docx)
    ok = True
    client = httpx.Client(base_url=BASE, timeout=60)
    body = {}

    # 1 拉模板
    r = client.get("/api/v1/templates", params={"page": 1, "page_size": 20})
    templates = r.json()
    tid = templates["items"][0]["template_id"] if templates.get("items") else None
    print(f"[1] GET /api/v1/templates -> {r.status_code}, total={templates.get('total')}, template_id={tid}")
    ok = ok and r.status_code == 200 and tid is not None

    # 2 上传
    with open(str(docx), "rb") as f:
        r = client.post(
            "/api/v1/reports",
            files={"file": (docx.name, f)},
            data={"template_id": tid},
        )
    up = r.json()
    rid = up.get("report_id")
    print(f"[2] POST /api/v1/reports -> {r.status_code}, report_id={rid}, status={up.get('status')}")
    ok = ok and r.status_code == 201 and rid is not None

    # 3 触发评阅
    r = client.post(f"/api/v1/reports/{rid}/grading")
    print(f"[3] POST /api/v1/reports/{rid}/grading -> {r.status_code}, status={r.json().get('status')}")
    ok = ok and r.status_code == 202

    # 4 轮询到终态
    status = None
    for _ in range(60):
        r = client.get(f"/api/v1/reports/{rid}/result")
        body = r.json()
        status = body.get("status")
        if status in TERMINAL:
            break
        time.sleep(1)
    print(
        f"[4] GET /api/v1/reports/{rid}/result -> {r.status_code}, status={status}, "
        f"total_score={body.get('total_score')}, items={len(body.get('items') or [])}, "
        f"student={body.get('student')}, comment非空={bool(body.get('comment'))}"
    )
    ok = ok and r.status_code == 200 and status in TERMINAL

    # 5 成绩列表
    r = client.get("/api/v1/grades", params={"page": 1, "page_size": 20})
    grades = r.json()
    print(f"[5] GET /api/v1/grades -> {r.status_code}, total={grades.get('total')}")
    ok = ok and r.status_code == 200

    # 6 原文段落：断言段落坐标自洽
    r = client.get(f"/api/v1/reports/{rid}/text")
    txt = r.json() if r.status_code == 200 else {}
    text = txt.get("text") or ""
    paras = txt.get("paragraphs") or []
    consistent = bool(paras)
    for p in paras:
        if text[p["start"]:p["end"]] != p["text"]:
            consistent = False
    if paras:
        consistent = consistent and paras[-1]["end"] == len(text)
    print(
        f"[6] GET /api/v1/reports/{rid}/text -> {r.status_code}, 段数={len(paras)}, "
        f"正文长度={len(text)}, 段落自洽={consistent}"
    )
    ok = ok and r.status_code == 200 and consistent

    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
