import pytest


@pytest.fixture(autouse=True)
def isolate_audit_db(tmp_path, monkeypatch):
    db_path = tmp_path / "gugugaga-test.sqlite3"
    monkeypatch.setenv("GUGUGAGA_DB_PATH", str(db_path))
    return db_path
