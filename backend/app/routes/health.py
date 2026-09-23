"""健康检查。本步唯一实现的 HTTP 接口，其余业务接口留到下一步。"""

from fastapi import APIRouter

from ..config import GLM_MODEL

router = APIRouter()


@router.get("/healthz")
def healthz():
    return {"status": "ok", "model": GLM_MODEL}
