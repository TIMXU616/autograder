"""部署入口：单端口同时提供后端 API 与前端页面。

为什么需要它
------------
项目是「前端静态资源 + FastAPI」两件事，而部署平台只暴露一个公网端口，
所以必须由同一个进程把两者都端出来。A 在《docs/部署记录.md》里写的部署包
入口就是这个 `run_server.py`，但它此前从未入库（只在部署暂存目录里存在），
导致「只从仓库出包」这条纪律落不了地 —— 本文件补齐这一环。

它做三件事
----------
1. 读平台注入的 `PORT`，绑定 `0.0.0.0`（本机开发默认 8000）。
2. 进程内 seed 模板：模板表为空会让 `/api/v1/templates` 返回 total=0，
   上传必报 4041。A 的部署记录里 9/22 18:35 那次发布失败就是这个原因，
   所以这里把 seed 做成启动的一部分，不依赖人工手跑 `scripts/seed.py`。
3. 挂载前端构建产物，并做 SPA fallback（前端用 history 路由，
   直接访问 `/result/<id>` 这类深链接必须回 `index.html`）。

本机开发**不需要**它：前端跑 `npm run dev`，后端跑 `uvicorn app.main:app`。
"""

import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402  导入即完成 init_db() 与启动恢复
from app.repositories import grading_repo  # noqa: E402

TEMPLATE_DIR = PROJECT_ROOT / "templates" / "grading"

# 前端构建产物的候选位置。`dist` 是 vite 默认输出，但发布平台会排除
# node_modules/.git/build output 之类的目录，所以留一个改名后的落点。
DIST_CANDIDATES = (
    PROJECT_ROOT / "frontend" / "dist",
    PROJECT_ROOT / "frontend" / "web",
    BACKEND_DIR / "static",
)


def seed_templates() -> None:
    """把 templates/grading/*.json 逐个导进库。幂等：已存在则跳过。

    与 scripts/seed.py 规则一致：单文件出错只打印该文件错误，不中断其余文件。
    """
    files = sorted(TEMPLATE_DIR.glob("*.json"))
    if not files:
        print(f"[seed] 跳过：目录下没有 *.json 模板文件 {TEMPLATE_DIR}", flush=True)
        return
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
            print(f"[seed] {flag}: {path.name} ({data['template_id']})", flush=True)
        except Exception as exc:  # 播种失败必须吼出来，否则表现成「上传一律 4041」
            print(f"[seed] 导入失败，已跳过 {path.name}：{type(exc).__name__}: {exc}", flush=True)


def mount_frontend() -> None:
    dist = next((p for p in DIST_CANDIDATES if (p / "index.html").exists()), None)
    if dist is None:
        print(
            "[static] 未找到前端构建产物，仅提供 API。候选路径："
            + ", ".join(str(p) for p in DIST_CANDIDATES),
            flush=True,
        )
        return

    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        # 已注册的路由（/api/**、/healthz、/docs）永远先匹配，走不到这里。
        # `/api/**` 的未注册路径必须保持框架的 JSON 404（{"detail":"Not Found"}）——
        # 前端靠「响应体里有没有 code 字段」区分「接口未上线」和「业务错误码」，
        # 这里若回 index.html 会让它把 404 误当成功渲染。
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        target = dist / full_path
        if full_path and target.is_file():
            return FileResponse(target)
        return FileResponse(dist / "index.html")  # history 路由深链接

    print(f"[static] 已挂载前端：{dist}", flush=True)


def main() -> None:
    seed_templates()
    mount_frontend()

    port = int(os.environ.get("PORT", "8000"))
    import uvicorn

    # 契约规定并发评分为串行，因此 workers 恒为 1，不可调。
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)


if __name__ == "__main__":
    main()
