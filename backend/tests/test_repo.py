"""入库层单测：幂等键冲突抛可识别异常。"""

import pytest

from app.errors import DuplicateReportError
from app.repositories import grading_repo


def test_insert_duplicate(tmp_db):
    grading_repo.insert_report("r1", "tpl-1", "a.docx", "same-sha", "uploaded")
    with pytest.raises(DuplicateReportError) as exc:
        grading_repo.insert_report("r2", "tpl-1", "a.docx", "same-sha", "uploaded")
    assert exc.value.code == 4091


def test_insert_template_idempotent(tmp_db):
    items = [{"item_id": 1, "name": "目的", "max_score": 10}]
    assert grading_repo.insert_template("tpl-1", "测试", "数据结构", 10, items) is True
    assert grading_repo.insert_template("tpl-1", "测试", "数据结构", 10, items) is False


def test_result_roundtrip(tmp_db):
    grading_repo.insert_report("r1", "tpl-1", "a.docx", "sha-1", "uploaded")
    items = [{"item_id": 1, "name": "目的", "max_score": 10, "score": 8.0}]
    grading_repo.insert_result(
        report_id="r1",
        attempt_no=1,
        model="glm-4.7",
        status="success",
        total_score=8.0,
        consistency=None,
        warnings=[],
        error_code=None,
        items=items,
    )
    r = grading_repo.get_result("r1", 1)
    assert r["status"] == "success"
    assert r["items"][0]["score"] == 8.0
