"""种子脚本：把评分点模板导入 grading_templates，重复执行不产生重复数据。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repositories import db, grading_repo  # noqa: E402

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates"
    / "grading"
    / "数据结构实验报告.json"
)


def main():
    db.init_db()
    data = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    inserted = grading_repo.insert_template(
        template_id=data["template_id"],
        name=data["name"],
        course=data["course"],
        total_score=data["total_score"],
        items=data["items"],
    )
    print("已插入模板" if inserted else "模板已存在，跳过")


if __name__ == "__main__":
    main()
