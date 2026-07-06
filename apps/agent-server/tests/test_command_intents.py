import json

from fastapi.testclient import TestClient

from app.main import app, build_command_summary, get_fixed_command_intent
from app.tools import command_whitelist


def test_node_version_intent_maps_to_fixed_command():
    assert get_fixed_command_intent("node版本") == "check_node"


def test_npm_version_intent_maps_to_fixed_command():
    assert get_fixed_command_intent("npm版本") == "check_npm"


def test_direct_command_tool_text_does_not_map_to_command():
    assert get_fixed_command_intent("command.check_node") is None


def test_failed_returncode_summary_contains_failure_code():
    summary = build_command_summary(
        "check_node",
        {
            "returncode": 7,
            "stdout": "",
            "stderr": "bad version",
            "stdout_truncated": False,
            "stderr_truncated": False,
        },
    )

    assert "7" in summary
    assert "失败码" in summary


def test_fixed_command_missing_executable_does_not_crash_websocket(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setattr(command_whitelist, "CONFIG_DIR", config_dir)
    (config_dir / "commands.local.json").write_text(
        json.dumps(
            {
                "check_node": {
                    "cmd": ["gugugaga-definitely-missing-executable"],
                    "cwd": None,
                    "risk": "low",
                    "desc": "Missing command for websocket failure test.",
                }
            }
        ),
        encoding="utf-8",
    )

    assistant_messages = []
    with TestClient(app).websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "user_message", "payload": {"text": "node版本"}})
        for _ in range(10):
            event = websocket.receive_json()
            if event["type"] == "assistant_message":
                assistant_messages.append(event["payload"]["text"])
            if event["type"] == "final":
                break

    assert any("命令执行失败，已写入审计日志" in message for message in assistant_messages)
