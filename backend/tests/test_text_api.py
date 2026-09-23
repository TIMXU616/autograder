"""原文段落接口单测：未解析返回 4090、报告不存在返回 4042、已解析正常返回。"""


def _seed_report(status, parsed_text=None, paragraphs=None):
    from app.repositories import grading_repo

    grading_repo.insert_template("tpl-1", "测试模板", "数据结构", 100, [])
    grading_repo.insert_report("rpt-t1", "tpl-1", "a.docx", "sha-1", status)
    if parsed_text is not None:
        grading_repo.save_parsed("rpt-t1", parsed_text, paragraphs or [])


def test_text_not_parsed(client):
    """只上传未触发评阅的报告调 /text：HTTP 200 + 4090，不得是 404。"""
    _seed_report("uploaded")
    r = client.get("/api/v1/reports/rpt-t1/text")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 4090
    assert body["detail"]["status"] == "uploaded"


def test_text_report_not_found(client):
    r = client.get("/api/v1/reports/no-such-id/text")
    assert r.status_code == 404
    assert r.json()["code"] == 4042


def test_text_parsed_ok(client):
    """已解析完成：返回正文与段落坐标，逐段自洽。"""
    text = "第一段\n第二段"
    paras = [
        {"start": 0, "end": 3, "text": "第一段"},
        {"start": 4, "end": 7, "text": "第二段"},
    ]
    _seed_report("success", text, paras)
    r = client.get("/api/v1/reports/rpt-t1/text")
    assert r.status_code == 200
    body = r.json()
    assert body["report_id"] == "rpt-t1"
    assert body["filename"] == "a.docx"
    assert body["text"] == text
    for p in body["paragraphs"]:
        assert body["text"][p["start"]:p["end"]] == p["text"]
