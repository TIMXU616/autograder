"""入口：只做装配与异常映射，零业务逻辑。"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .constants import HTTP_STATUS_BY_CODE
from .errors import GradingError
from .repositories import db, grading_repo
from .routes import grades, health, reports, templates


def _first_validation_message(exc: RequestValidationError) -> str:
    """把 FastAPI 校验失败的第一个错误拼成中文提示，供契约错误体使用。"""
    errors = exc.errors()
    if not errors:
        return "请求参数非法"
    err = errors[0]
    err_type = err.get("type", "")
    loc = err.get("loc", [])
    field = str(loc[-1]) if loc else "参数"
    ctx = err.get("ctx") or {}
    if err_type == "less_than_equal":
        return f"{field} 最大为 {ctx.get('le')}"
    if err_type == "greater_than_equal":
        return f"{field} 最小为 {ctx.get('ge')}"
    if err_type == "missing":
        return f"缺少必填字段 {field}"
    return err.get("msg") or "请求参数非法"


def create_app() -> FastAPI:
    db.init_db()
    # 启动恢复：把上次未跑完的 in-flight 报告置 failed，避免重启后永久卡死
    recovered = grading_repo.mark_inflight_failed()
    if recovered:
        logging.getLogger(__name__).warning("启动恢复：%s 条 in-flight 报告已置 failed", recovered)
    app = FastAPI(title="AutoGrader")

    @app.exception_handler(GradingError)
    def grading_error_handler(request: Request, exc: GradingError):
        status = getattr(exc, "http_status", None) or HTTP_STATUS_BY_CODE.get(exc.code, 400)
        return JSONResponse(
            status_code=status,
            content={
                "code": exc.code,
                "message": exc.message,
                "detail": getattr(exc, "detail", None),
            },
        )

    @app.exception_handler(RequestValidationError)
    def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"code": 4002, "message": _first_validation_message(exc), "detail": None},
        )

    app.include_router(health.router)
    app.include_router(reports.router)
    app.include_router(templates.router)
    app.include_router(grades.router)
    return app


app = create_app()
