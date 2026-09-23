"""控制层：上传校验、评阅串行队列、状态机推进、结果组装。"""

import hashlib
import json
import logging
import queue
import threading
import uuid
from pathlib import Path

from ..config import GLM_MODEL
from ..constants import ERR_NO_TEXT_LAYER, PARSE_ERROR_CODES
from ..errors import (
    DuplicateReportError,
    EmptyFileError,
    GradingError,
    NotParsedError,
    TooLargeError,
    UnsupportedTypeError,
)
from ..repositories import grading_repo
from ..services import grader, parser

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
MAX_BYTES = 20 * 1024 * 1024
SUPPORTED_EXTS = {".docx", ".pdf"}

IN_FLIGHT = ("parsing", "parsed", "grading")
TERMINAL = ("success", "partial_success", "failed")

# 串行队列：并发上限 1，同一时刻只有一个评阅任务在跑
_task_queue = queue.Queue()


def upload_report(file_bytes: bytes, filename: str, template_id: str) -> dict:
    """上传：校验 → 落盘 → 落库，不启动解析。"""
    if not file_bytes:
        raise EmptyFileError()
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTS:
        raise UnsupportedTypeError()
    if len(file_bytes) > MAX_BYTES:
        raise TooLargeError()
    grading_repo.get_template(template_id)  # 不存在抛 4041

    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    report_id = uuid.uuid4().hex
    uploaded_at = grading_repo.now_cst()
    student = Path(filename).stem.strip() or None  # 文件名去扩展名、去首尾空格，空则 None

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / (report_id + ext)
    file_path.write_bytes(file_bytes)

    try:
        grading_repo.insert_report(
            report_id, template_id, filename, file_sha256, "uploaded", uploaded_at, student
        )
    except DuplicateReportError as exc:
        file_path.unlink(missing_ok=True)  # 幂等冲突时清理刚落盘的文件，避免 uploads/ 残留垃圾
        existing = grading_repo.find_report_by_key(file_sha256, template_id)
        exc.detail = {"report_id": existing["report_id"] if existing else None}
        raise exc

    return {
        "report_id": report_id,
        "template_id": template_id,
        "filename": filename,
        "file_sha256": file_sha256,
        "status": "uploaded",
        "uploaded_at": uploaded_at,
    }


def trigger_grading(report_id: str) -> dict:
    """触发评阅：状态检查后投进串行队列。"""
    report = grading_repo.get_report(report_id)  # 不存在抛 4042
    status = report["status"]
    accepted = grading_repo.now_cst()

    if status in IN_FLIGHT:
        return {"report_id": report_id, "status": status, "attempt_no": 1, "accepted_at": accepted}
    if status in TERMINAL:
        raise DuplicateReportError("该报告已完成评阅，不可重复触发")

    grading_repo.update_report_status(report_id, "parsing")
    _task_queue.put(report_id)
    return {"report_id": report_id, "status": "parsing", "attempt_no": 1, "accepted_at": accepted}


def get_result(report_id: str) -> dict:
    """组装评阅结果。student 由上传文件名去扩展名派生。"""
    report = grading_repo.get_report(report_id)
    filename = report["filename"]

    result = None
    if report["status"] in TERMINAL:
        try:
            result = grading_repo.get_result(report_id, 1)
        except Exception:
            result = None

    return {
        "report_id": report_id,
        "template_id": report["template_id"],
        "filename": filename,
        "student": Path(filename).stem,
        "status": result["status"] if result else report["status"],
        "attempt_no": result["attempt_no"] if result else 1,
        "model": GLM_MODEL,
        "total_score": result["total_score"] if result else None,
        "consistency": result["consistency"] if result else None,
        "comment": (result.get("comment") if result else None),
        "highlights": (result["highlights"] if result else []),
        "suggestions": (result["suggestions"] if result else []),
        "warnings": result["warnings"] if result else [],
        "error_code": result["error_code"] if result else None,
        "items": result["items"] if result else [],
        "grading_started_at": result["grading_started_at"] if result else None,
        "finished_at": result["finished_at"] if result else None,
    }


def get_report_text(report_id: str) -> dict:
    """原文段落接口用：直接读落库的解析结果，不得每次请求重新解析文件。"""
    report = grading_repo.get_report(report_id)  # 不存在抛 4042

    if report["status"] in ("uploaded", "parsing"):
        raise NotParsedError(report["status"])

    if not report.get("parsed_text"):
        # 解析阶段就失败的报告：回传其解析类错误码与文案，HTTP 200
        code = None
        message = "报告解析失败"
        try:
            result = grading_repo.get_result(report_id, 1)
            code = result["error_code"]
            if result["warnings"]:
                message = result["warnings"][0]
        except Exception:
            pass
        if code in PARSE_ERROR_CODES:
            raise GradingError(code, message, http_status=200)
        raise GradingError(ERR_NO_TEXT_LAYER, message, http_status=200)

    return {
        "report_id": report_id,
        "filename": report["filename"],
        "text": report["parsed_text"],
        "paragraphs": json.loads(report["parsed_paragraphs"] or "[]"),
    }


def _process_report(report_id: str) -> None:
    """队列任务：解析 → 评分 → 入库，推进状态机。"""
    report = grading_repo.get_report(report_id)
    template = grading_repo.get_template(report["template_id"])
    ext = Path(report["filename"]).suffix.lower()
    path = UPLOAD_DIR / (report_id + ext)
    started = grading_repo.now_cst()

    try:
        parsed = parser.parse_file(str(path))
    except GradingError as exc:
        _finish_failed(report_id, exc, started)
        return

    grading_repo.save_parsed(report_id, parsed["text"], parsed["paragraphs"])
    grading_repo.update_report_status(report_id, "parsed")
    grading_repo.update_report_status(report_id, "grading")

    try:
        result = grader.grade_report(template, parsed["text"])
    except GradingError as exc:
        _finish_failed(report_id, exc, started)
        return

    status = _derive_status(result["items"])
    grading_repo.insert_result(
        report_id=report_id,
        attempt_no=1,
        model=GLM_MODEL,
        status=status,
        total_score=result["total_score"],
        consistency=None,
        warnings=result["warnings"],
        error_code=None,
        items=result["items"],
        grading_started_at=started,
        finished_at=grading_repo.now_cst(),
        comment=result.get("comment"),
        highlights=result.get("highlights"),
        suggestions=result.get("suggestions"),
    )
    grading_repo.update_report_status(report_id, status)


def _finish_failed(report_id: str, exc: GradingError, started: str) -> None:
    grading_repo.update_report_status(report_id, "failed")
    grading_repo.insert_result(
        report_id=report_id,
        attempt_no=1,
        model=GLM_MODEL,
        status="failed",
        total_score=None,
        consistency=None,
        warnings=[exc.message],
        error_code=exc.code,
        items=[],
        grading_started_at=started,
        finished_at=grading_repo.now_cst(),
        comment=None,
        highlights=[],
        suggestions=[],
    )


def _derive_status(items) -> str:
    statuses = [it.get("status") for it in items]
    if not statuses:
        return "failed"
    if all(s == "graded" for s in statuses):
        return "success"
    if any(s == "graded" for s in statuses):
        return "partial_success"
    return "failed"


def _worker_loop():
    while True:
        report_id = _task_queue.get()
        try:
            _process_report(report_id)
        except Exception:
            logger.exception("评阅任务异常，报告置 failed: %s", report_id)
            try:
                grading_repo.update_report_status(report_id, "failed")
            except Exception:
                pass
        finally:
            _task_queue.task_done()


_worker = threading.Thread(target=_worker_loop, daemon=True)
_worker.start()


def run_grading(report_path, template: dict) -> dict:
    """端到端脚本用：解析 → 评分 → 入库 → 读回。"""
    parsed = parser.parse_file(report_path)
    file_bytes = Path(report_path).read_bytes()
    file_sha256 = hashlib.sha256(file_bytes).hexdigest()
    report_id = uuid.uuid4().hex
    filename = Path(report_path).name

    grading_repo.insert_report(report_id, template["template_id"], filename, file_sha256, "uploaded")

    started = grading_repo.now_cst()
    result = grader.grade_report(template, parsed["text"])
    finished = grading_repo.now_cst()
    status = _derive_status(result["items"])

    grading_repo.insert_result(
        report_id=report_id,
        attempt_no=1,
        model=GLM_MODEL,
        status=status,
        total_score=result["total_score"],
        consistency=None,
        warnings=result["warnings"],
        error_code=None,
        items=result["items"],
        grading_started_at=started,
        finished_at=finished,
        comment=result.get("comment"),
        highlights=result.get("highlights"),
        suggestions=result.get("suggestions"),
    )
    grading_repo.update_report_status(report_id, status)
    return grading_repo.get_result(report_id, 1)
