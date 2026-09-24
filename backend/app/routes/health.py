"""健康检查。mock 模式下显式自曝，方便一眼分辨是否走了真实模型。

注意：部署到公网后平台探活会拦截 /healthz 并返回它自己的 JSON，
因此前端不要依赖本接口判断 mock，以结果体 warnings 里的固定串为准。
"""

from fastapi import APIRouter

from ..config import GLM_API_KEY, GLM_MODEL

router = APIRouter()


@router.get("/healthz")
def healthz():
    if GLM_API_KEY:
        return {"status": "ok", "model": GLM_MODEL, "mock": False}
    return {"status": "ok", "model": "mock", "mock": True}
