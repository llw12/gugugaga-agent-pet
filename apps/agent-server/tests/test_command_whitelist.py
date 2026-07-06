import json
import sqlite3
import sys

import pytest

from app.security.permissions import PermissionDenied
from app.storage.db import get_db_path
from app.tools import command_whitelist
from app.tools.command_whitelist import CommandConfigError, CommandNotAllowed, CommandRejected
from app.tools.registry import execute_tool


@pytest.fixture()
def command_config_dir(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr(command_whitelist, "CONFIG_DIR", config_dir)
    return config_dir


def write_local_commands(config_dir, commands):
    (config_dir / "commands.local.json").write_text(json.dumps(commands), encoding="utf-8")


def write_raw_local_commands(config_dir, content: str):
    (config_dir / "commands.local.json").write_text(content, encoding="utf-8")


def write_example_commands(config_dir, commands):
    (config_dir / "commands.example.json").write_text(json.dumps(commands), encoding="utf-8")


def fetch_tool_call_status(tool_name: str) -> str:
    with sqlite3.connect(get_db_path()) as connection:
        row = connection.execute(
            "SELECT status FROM tool_calls WHERE tool_name = ? ORDER BY id DESC LIMIT 1",
            (tool_name,),
        ).fetchone()
    assert row is not None
    return row[0]


def fetch_audit_event(event_type: str) -> str:
    with sqlite3.connect(get_db_path()) as connection:
        row = connection.execute(
            "SELECT event_type FROM audit_logs WHERE event_type = ? ORDER BY id DESC LIMIT 1",
            (event_type,),
        ).fetchone()
    assert row is not None
    return row[0]


def test_whitelisted_command_executes(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "python_version": {
                "cmd": [sys.executable, "-c", "print('ok')"],
                "cwd": None,
                "risk": "low",
                "desc": "Test read-only Python command.",
            }
        },
    )

    result = execute_tool("command.python_version")

    assert result["returncode"] == 0
    assert result["stdout"].strip() == "ok"
    assert fetch_tool_call_status("command.python_version") == "success"


def test_sensitive_env_vars_are_not_visible_to_child_process(command_config_dir, monkeypatch):
    monkeypatch.setenv("GUGUGAGA_TEST_SECRET", "secret-value")
    monkeypatch.setenv("GUGUGAGA_TEST_TOKEN", "token-value")
    write_local_commands(
        command_config_dir,
        {
            "env_probe": {
                "cmd": [
                    sys.executable,
                    "-c",
                    (
                        "import os; "
                        "print(os.getenv('GUGUGAGA_TEST_SECRET')); "
                        "print(os.getenv('GUGUGAGA_TEST_TOKEN'))"
                    ),
                ],
                "cwd": None,
                "risk": "low",
                "desc": "Probe child process environment.",
            }
        },
    )

    result = execute_tool("command.env_probe")

    assert result["returncode"] == 0
    assert result["stdout"].splitlines() == ["None", "None"]
    assert fetch_tool_call_status("command.env_probe") == "success"


def test_path_is_preserved_so_executable_lookup_still_works(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "python_from_path": {
                "cmd": ["python", "-c", "print('path-ok')"],
                "cwd": None,
                "risk": "low",
                "desc": "Resolve Python from PATH.",
            }
        },
    )

    result = execute_tool("command.python_from_path")

    assert result["returncode"] == 0
    assert result["stdout"].strip() == "path-ok"
    assert fetch_tool_call_status("command.python_from_path") == "success"


def test_missing_local_whitelist_rejects_command(command_config_dir):
    with pytest.raises(CommandNotAllowed):
        execute_tool("command.check_node")

    assert fetch_tool_call_status("command.check_node") == "rejected"


def test_example_whitelist_is_not_loaded_at_runtime(command_config_dir):
    write_example_commands(
        command_config_dir,
        {
            "check_node": {
                "cmd": [sys.executable, "-c", "print('example')"],
                "cwd": None,
                "risk": "low",
                "desc": "Example only.",
            }
        },
    )

    with pytest.raises(CommandNotAllowed):
        execute_tool("command.check_node")

    assert fetch_tool_call_status("command.check_node") == "rejected"


def test_invalid_local_json_rejects_and_writes_audit(command_config_dir):
    write_raw_local_commands(command_config_dir, "{not valid json")

    with pytest.raises(CommandConfigError):
        execute_tool("command.check_node")

    assert fetch_tool_call_status("command.check_node") == "rejected"
    assert fetch_audit_event("command_config_error") == "command_config_error"


def test_command_not_in_whitelist_is_rejected(command_config_dir):
    write_local_commands(command_config_dir, {})

    with pytest.raises(CommandNotAllowed):
        execute_tool("command.not_listed")

    assert fetch_tool_call_status("command.not_listed") == "rejected"


def test_non_object_command_entry_is_config_error(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "_note": "metadata strings remain allowed for comments",
            "bad_entry": ["not", "an", "object"],
        },
    )

    with pytest.raises(CommandConfigError):
        execute_tool("command.bad_entry")

    assert fetch_tool_call_status("command.bad_entry") == "rejected"
    assert fetch_audit_event("command_config_error") == "command_config_error"


def test_invalid_risk_is_treated_as_blocked(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "invalid_risk": {
                "cmd": [sys.executable, "-c", "print('nope')"],
                "cwd": None,
                "risk": "surprise",
                "desc": "Invalid risk should be blocked.",
            }
        },
    )

    with pytest.raises(PermissionDenied):
        execute_tool("command.invalid_risk")

    assert fetch_tool_call_status("command.invalid_risk") == "rejected"


def test_long_stdout_and_stderr_are_truncated(command_config_dir):
    max_chars = command_whitelist.OUTPUT_MAX_CHARS
    write_local_commands(
        command_config_dir,
        {
            "long_output": {
                "cmd": [
                    sys.executable,
                    "-c",
                    "import sys; print('o' * 21000); print('e' * 21000, file=sys.stderr)",
                ],
                "cwd": None,
                "risk": "low",
                "desc": "Emit long output.",
            }
        },
    )

    result = execute_tool("command.long_output")

    assert result["returncode"] == 0
    assert len(result["stdout"]) == max_chars
    assert len(result["stderr"]) == max_chars
    assert result["stdout_truncated"] is True
    assert result["stderr_truncated"] is True
    assert fetch_tool_call_status("command.long_output") == "success"


def test_shell_string_command_is_rejected(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "shell_string": {
                "cmd": f"{sys.executable} -c print('nope')",
                "cwd": None,
                "risk": "low",
                "desc": "Invalid string command.",
            }
        },
    )

    with pytest.raises(CommandRejected):
        execute_tool("command.shell_string")

    assert fetch_tool_call_status("command.shell_string") == "rejected"


def test_non_null_cwd_is_rejected(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "custom_cwd": {
                "cmd": [sys.executable, "-c", "print('nope')"],
                "cwd": ".",
                "risk": "low",
                "desc": "Custom cwd is disabled in this phase.",
            }
        },
    )

    with pytest.raises(CommandRejected):
        execute_tool("command.custom_cwd")

    assert fetch_tool_call_status("command.custom_cwd") == "rejected"


def test_medium_risk_command_is_rejected(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "medium_command": {
                "cmd": [sys.executable, "-c", "print('nope')"],
                "cwd": None,
                "risk": "medium",
                "desc": "Medium risk command must not execute.",
            }
        },
    )

    with pytest.raises(PermissionDenied):
        execute_tool("command.medium_command")

    assert fetch_tool_call_status("command.medium_command") == "rejected"


def test_safe_risk_command_is_rejected_for_whitelist(command_config_dir):
    write_local_commands(
        command_config_dir,
        {
            "safe_command": {
                "cmd": [sys.executable, "-c", "print('nope')"],
                "cwd": None,
                "risk": "safe",
                "desc": "External commands must be low risk, not safe.",
            }
        },
    )

    with pytest.raises(PermissionDenied):
        execute_tool("command.safe_command")

    assert fetch_tool_call_status("command.safe_command") == "rejected"
