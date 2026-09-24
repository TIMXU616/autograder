"""端到端脚本：解析 → 评分 → 入库 → 从库里读回并打印完整结果。

用法：python scripts/run_one_report.py <报告文件路径>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.controllers.grading_controller import run_grading  # noqa: E402
from app.repositories import db  # noqa: E402

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "grading"
    / "数据结构实验报告.json"
)


def main():
    if len(sys.argv) < 2:
        print("用法：python scripts/run_one_report.py <报告文件路径>")
        sys.exit(1)

    report_path = sys.argv[1]
    db.init_db()
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    result = run_grading(report_path, template)

    print(f"report_id: {result['report_id']}")
    print(f"status: {result['status']}")
    print(f"model: {result['model']}")
    print(f"total_score: {result['total_score']}")
    print(f"warnings: {json.dumps(result['warnings'], ensure_ascii=False)}")
    print("items:")
    for it in result["items"]:
        ev = (it.get("evidence") or "")[:30]
        rs = (it.get("reason") or "")[:30]
        print(
            f"  item {it['item_id']}: score={it['score']}, level={it['level']}, "
            f"evidence={ev}, status={it['status']}, reason={rs}"
        )


if __name__ == "__main__":
    main()
