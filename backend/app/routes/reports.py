"""报告相关路由：上传、触发评阅、查询结果。路由层只做参数校验与编排。"""

from fastapi import APIRouter, File, Form, UploadFile

from ..controllers import grading_controller as ctrl

router = APIRouter()


@router.post("/api/v1/reports", status_code=201)
async def upload_report(file: UploadFile = File(...), template_id: str = Form(...)):
    """上传报告：只落库不启动解析。异常由 main.py 的处理器映射为契约错误码。"""
    content = await file.read()
    return ctrl.upload_report(content, file.filename or "", template_id)


@router.post("/api/v1/reports/{report_id}/grading", status_code=202)
def trigger_grading(report_id: str):
    """触发评阅：投进串行队列。"""
    return ctrl.trigger_grading(report_id)


@router.get("/api/v1/reports/{report_id}/result")
def get_result(report_id: str):
    """查询评阅结果与状态机当前状态。"""
    return ctrl.get_result(report_id)
