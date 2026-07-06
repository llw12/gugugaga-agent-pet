import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "gugugaga.sqlite3"
DB_PATH = Path(os.environ.get("GUGUGAGA_DB_PATH", DEFAULT_DB_PATH))


def get_db_path() -> Path:
    configured_path = os.environ.get("GUGUGAGA_DB_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return DB_PATH


def init_db(db_path: Path | None = None) -> None:
    resolved_path = db_path or get_db_path()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(resolved_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_type TEXT NOT NULL,
              detail TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tool_calls (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              tool_name TEXT NOT NULL,
              risk_level TEXT NOT NULL,
              status TEXT NOT NULL,
              detail TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
