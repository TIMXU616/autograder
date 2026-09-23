"""数据库连接与建表。SQLite 单文件，三张表字段与契约第 5 节一一对应。"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "autograder.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    report_id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_sha256 TEXT NOT NULL,
    status TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    student TEXT,
    parsed_text TEXT,
    parsed_paragraphs TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_sha_template
    ON reports (file_sha256, template_id);

CREATE TABLE IF NOT EXISTS grading_templates (
    template_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    course TEXT NOT NULL,
    total_score INTEGER NOT NULL,
    items TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS grading_results (
    report_id TEXT NOT NULL,
    attempt_no INTEGER NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,
    total_score REAL,
    consistency REAL,
    warnings TEXT,
    error_code INTEGER,
    items TEXT,
    comment TEXT,
    highlights TEXT,
    suggestions TEXT,
    grading_started_at TEXT,
    finished_at TEXT,
    PRIMARY KEY (report_id, attempt_no)
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(_SCHEMA)
        # 兼容已存在的旧表：补 P2-06B 字段扩展新增的三列
        for col, decl in (("comment", "TEXT"), ("highlights", "TEXT"), ("suggestions", "TEXT")):
            try:
                conn.execute(f"ALTER TABLE grading_results ADD COLUMN {col} {decl}")
            except sqlite3.OperationalError:
                pass  # 列已存在，跳过
        # 兼容已存在的旧表：reports 补 student 列
        for col in ("student", "parsed_text", "parsed_paragraphs"):
            try:
                conn.execute(f"ALTER TABLE reports ADD COLUMN {col} TEXT")
            except sqlite3.OperationalError:
                pass  # 列已存在，跳过
        conn.commit()
    finally:
        conn.close()
