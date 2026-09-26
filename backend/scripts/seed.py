"""种子脚本：把 templates/grading/*.json 逐个导入 grading_templates。

重复执行不产生重复数据；单个文件出错只打印该文件错误，不中断其余文件。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repositories import db, grading_repo  # noqa: E402

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "grading"


def seed_templates(template_dir=None) -> int:
    """遍历目录下所有 *.json 逐个导入，返回成功导入的文件数。"""
    directory = Path(template_dir) if template_dir else TEMPLATE_DIR
    files = sorted(directory.glob("*.json"))
    if not files:
        print(f"跳过：目录 {directory} 下没有找到任何 *.json 模板文件")
        return 0

    ok = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            inserted = grading_repo.insert_template(
                template_id=data["template_id"],
                name=data["name"],
                course=data["course"],
                total_score=data["total_score"],
                items=data["items"],
                domain_terms=data.get("domain_terms"),
            )
            flag = "已插入模板" if inserted else "模板已存在，跳过"
            print(f"{flag}: {path.name} ({data['template_id']})")
            ok += 1
        except Exception as exc:
            print(f"导入失败，已跳过该文件: {path.name} —— {type(exc).__name__}: {exc}")
    return ok


def main():
    db.init_db()
    seed_templates()


if __name__ == "__main__":
    main()
