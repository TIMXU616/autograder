"""模板列表路由：真读种子数据，支持分页与课程过滤。"""

from fastapi import APIRouter, Query

from ..repositories import grading_repo

router = APIRouter()


@router.get("/api/v1/templates")
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    course: str = Query(None),
):
    return grading_repo.list_templates(page=page, page_size=page_size, course=course or None)
