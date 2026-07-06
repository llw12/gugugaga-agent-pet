import json
import sqlite3
from typing import Any

from app.storage.db import get_db_path, init_db


def log_event(event_type: str, detail: dict[str, Any]) -> None:
    db_path = get_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO audit_logs (event_type, detail) VALUES (?, ?)",
            (event_type, json.dumps(detail, ensure_ascii=False)),
        )


def log_tool_call(tool_name: str, risk_level: str, status: str, detail: dict[str, Any] | None = None) -> None:
    db_path = get_db_path()
    init_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO tool_calls (tool_name, risk_level, status, detail) VALUES (?, ?, ?, ?)",
            (tool_name, risk_level, status, json.dumps(detail or {}, ensure_ascii=False)),
        )
