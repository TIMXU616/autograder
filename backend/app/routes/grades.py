"""成绩列表路由：从 grading_results 读终态记录，支持分页、过滤、排序。"""

from fastapi import APIRouter, Query

from ..repositories import grading_repo

router = APIRouter()


@router.get("/api/v1/grades")
def list_grades(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    template_id: str = Query(None),
    order: str = Query("total_score_desc"),
):
    if order not in ("total_score_desc", "total_score_asc"):
        from ..errors import InvalidParamError

        raise InvalidParamError("order 取值非法，仅支持 total_score_desc / total_score_asc")
    return grading_repo.list_grades(
        page=page, page_size=page_size, template_id=template_id, order=order
    )
