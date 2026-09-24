"""pytest 共享 fixture：临时数据库 + sys.path。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from app.repositories import db  # noqa: E402


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    return tmp_path / "test.db"


@pytest.fixture
def client(tmp_db):
    """基于临时数据库重建 app，避免接口单测污染真实库。"""
    from fastapi.testclient import TestClient

    from app.main import create_app

    return TestClient(create_app())
