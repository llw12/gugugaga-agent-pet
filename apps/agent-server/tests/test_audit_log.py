import sqlite3

import pytest

from app.main import record_approval_result
from app.security.permissions import PermissionDenied
from app.storage.db import get_db_path
from app.tools.registry import execute_tool


def fetch_status(table: str, name_column: str, name: str) -> str:
    with sqlite3.connect(get_db_path()) as connection:
        row = connection.execute(
            f"SELECT status FROM {table} WHERE {name_column} = ? ORDER BY id DESC LIMIT 1",
            (name,),
        ).fetchone()
    assert row is not None
    return row[0]


def fetch_event_type(event_type: str) -> str:
    with sqlite3.connect(get_db_path()) as connection:
        row = connection.execute(
            "SELECT event_type FROM audit_logs WHERE event_type = ? ORDER BY id DESC LIMIT 1",
            (event_type,),
        ).fetchone()
    assert row is not None
    return row[0]


def test_safe_tool_writes_success_tool_call():
    execute_tool("system.get_overview")

    assert fetch_status("tool_calls", "tool_name", "system.get_overview") == "success"


def test_medium_tool_rejection_writes_rejected_tool_call():
    with pytest.raises(PermissionDenied):
        execute_tool("mock.medium_approval")

    assert fetch_status("tool_calls", "tool_name", "mock.medium_approval") == "rejected"


def test_unknown_approval_result_writes_rejected_audit_log():
    accepted, message = record_approval_result("missing", approved=True)

    assert accepted is False
    assert message
    assert fetch_event_type("approval_result_rejected") == "approval_result_rejected"
