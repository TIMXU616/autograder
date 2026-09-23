"""入库层：三张表的读写。幂等键冲突抛可识别异常，供上层映射 4091。"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..errors import DuplicateReportError, ReportNotFoundError, TemplateNotFoundError
from .db import get_conn

_CST = timezone(timedelta(hours=8))


def now_cst() -> str:
    """ISO 8601 带 +08:00。不依赖系统时区库，Windows 上 tzdata 常缺失。"""
    return datetime.now(_CST).isoformat()


def insert_report(report_id, template_id, filename, file_sha256, status, uploaded_at=None, student=None) -> None:
    uploaded_at = uploaded_at or now_cst()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO reports (report_id, template_id, filename, file_sha256, status, uploaded_at, student) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (report_id, template_id, filename, file_sha256, status, uploaded_at, student),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise DuplicateReportError() from exc
    finally:
        conn.close()


def get_report(report_id) -> dict:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE report_id = ?", (report_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise ReportNotFoundError()
    return dict(row)


def insert_template(template_id, name, course, total_score, items, created_at=None) -> bool:
    """返回 True 表示新插入，False 表示已存在（幂等跳过）。"""
    created_at = created_at or now_cst()
    conn = get_conn()
    try:
        exists = conn.execute(
            "SELECT 1 FROM grading_templates WHERE template_id = ?", (template_id,)
        ).fetchone()
        if exists:
            return False
        conn.execute(
            "INSERT INTO grading_templates (template_id, name, course, total_score, items, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (template_id, name, course, total_score, json.dumps(items, ensure_ascii=False), created_at),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def insert_result(
    report_id, attempt_no, model, status, total_score, consistency,
    warnings, error_code, items, grading_started_at=None, finished_at=None,
    comment=None, highlights=None, suggestions=None,
) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO grading_results "
            "(report_id, attempt_no, model, status, total_score, consistency, warnings, error_code, items, "
            "comment, highlights, suggestions, grading_started_at, finished_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                report_id, attempt_no, model, status, total_score, consistency,
                json.dumps(warnings, ensure_ascii=False), error_code,
                json.dumps(items, ensure_ascii=False),
                comment, json.dumps(highlights or [], ensure_ascii=False),
                json.dumps(suggestions or [], ensure_ascii=False),
                grading_started_at, finished_at,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_result(report_id, attempt_no=1) -> dict:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM grading_results WHERE report_id = ? AND attempt_no = ?",
            (report_id, attempt_no),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise ReportNotFoundError()
    d = dict(row)
    d["warnings"] = json.loads(d["warnings"] or "[]")
    d["items"] = json.loads(d["items"] or "[]")
    d["highlights"] = json.loads(d["highlights"] or "[]")
    d["suggestions"] = json.loads(d["suggestions"] or "[]")
    return d


def list_templates(page=1, page_size=20, course=None) -> dict:
    """模板列表，items 只返回 item_id / name / max_score 摘要。"""
    where = ""
    params = []
    if course:
        where = " WHERE course = ?"
        params.append(course)

    conn = get_conn()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM grading_templates" + where, params
        ).fetchone()[0]
        offset = (page - 1) * page_size
        rows = conn.execute(
            "SELECT * FROM grading_templates" + where + " ORDER BY template_id LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
    finally:
        conn.close()

    items = []
    for r in rows:
        d = dict(r)
        raw_items = json.loads(d["items"] or "[]")
        d["items"] = [
            {"item_id": it["item_id"], "name": it["name"], "max_score": it["max_score"]}
            for it in raw_items
        ]
        items.append(d)
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def update_report_status(report_id, status) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE reports SET status = ? WHERE report_id = ?", (status, report_id))
        conn.commit()
    finally:
        conn.close()


def get_template(template_id) -> dict:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM grading_templates WHERE template_id = ?", (template_id,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise TemplateNotFoundError()
    d = dict(row)
    d["items"] = json.loads(d["items"] or "[]")
    return d


def list_grades(page=1, page_size=20, template_id=None, order="total_score_desc") -> dict:
    """成绩列表，只列终态 success / partial_success 的记录。"""
    where = " WHERE r.status IN ('success', 'partial_success')"
    params = []
    if template_id:
        where += " AND p.template_id = ?"
        params.append(template_id)

    order_sql = "r.total_score ASC" if order == "total_score_asc" else "r.total_score DESC"

    conn = get_conn()
    try:
        total = conn.execute(
            "SELECT COUNT(*) FROM grading_results r JOIN reports p ON r.report_id = p.report_id" + where,
            params,
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT r.report_id, r.total_score, r.status, r.finished_at, "
            "p.filename, p.template_id, t.name AS template_name "
            "FROM grading_results r "
            "JOIN reports p ON r.report_id = p.report_id "
            "LEFT JOIN grading_templates t ON p.template_id = t.template_id"
            + where + " ORDER BY " + order_sql + " LIMIT ? OFFSET ?",
            params + [page_size, (page - 1) * page_size],
        ).fetchall()
    finally:
        conn.close()

    items = []
    for r in rows:
        d = dict(r)
        d["student"] = Path(d["filename"]).stem  # 与 get_result 同口径派生
        items.append(d)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def mark_inflight_failed() -> int:
    """服务启动时把 in-flight 报告置 failed，避免重启后卡死。返回受影响行数。"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "UPDATE reports SET status = 'failed' WHERE status IN ('parsing', 'parsed', 'grading')"
        )
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def find_report_by_key(file_sha256, template_id):
    """按幂等键查已有报告，供 4091 响应回填 report_id。"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE file_sha256 = ? AND template_id = ?",
            (file_sha256, template_id),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None
