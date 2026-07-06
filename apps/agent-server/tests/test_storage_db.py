from app.storage.db import get_db_path


def test_db_path_uses_test_environment(isolate_audit_db):
    assert get_db_path() == isolate_audit_db
