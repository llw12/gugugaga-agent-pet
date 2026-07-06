import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.security.audit_log import log_event, log_tool_call
from app.security.permissions import PermissionDenied, RiskLevel, ensure_allowed

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
LOCAL_COMMANDS_FILE = "commands.local.json"
COMMAND_TOOL_PREFIX = "command."
COMMAND_TIMEOUT_SECONDS = 10
OUTPUT_MAX_CHARS = 20000
SENSITIVE_ENV_MARKERS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD")
PASSTHROUGH_ENV_NAMES = ("PATH", "PATHEXT", "SYSTEMROOT", "WINDIR")


class CommandNotAllowed(RuntimeError):
    pass


class CommandRejected(RuntimeError):
    pass


class CommandConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class WhitelistedCommand:
    name: str
    cmd: Any
    cwd: str | None
    risk_level: RiskLevel
    description: str


def get_config_path() -> Path:
    return CONFIG_DIR / LOCAL_COMMANDS_FILE


def log_config_error(message: str) -> None:
    log_event(
        "command_config_error",
        {
            "config": str(get_config_path()),
            "reason": message,
        },
    )


def load_commands() -> dict[str, WhitelistedCommand]:
    config_path = get_config_path()
    if not config_path.exists():
        return {}

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            raw_commands = json.load(config_file)
    except json.JSONDecodeError as error:
        message = f"invalid JSON in {LOCAL_COMMANDS_FILE}: {error.msg}"
        log_config_error(message)
        raise CommandConfigError(message) from error

    if not isinstance(raw_commands, dict):
        message = f"{LOCAL_COMMANDS_FILE} must contain a JSON object"
        log_config_error(message)
        raise CommandConfigError(message)

    commands: dict[str, WhitelistedCommand] = {}
    for name, value in raw_commands.items():
        if name.startswith("_"):
            continue
        if not isinstance(value, dict):
            message = f"command entry {name!r} must be an object"
            log_config_error(message)
            raise CommandConfigError(message)

        risk = value.get("risk", RiskLevel.BLOCKED.value)
        try:
            risk_level = RiskLevel(risk)
        except ValueError:
            risk_level = RiskLevel.BLOCKED

        commands[name] = WhitelistedCommand(
            name=name,
            cmd=value.get("cmd"),
            cwd=value.get("cwd"),
            risk_level=risk_level,
            description=str(value.get("desc") or ""),
        )
    return commands


def validate_command(command: WhitelistedCommand) -> list[str]:
    if command.risk_level is not RiskLevel.LOW:
        raise PermissionDenied("whitelisted commands must be low risk")
    if not isinstance(command.cmd, list) or not command.cmd:
        raise CommandRejected("whitelisted commands must use a non-empty array command")
    if not all(isinstance(part, str) and part for part in command.cmd):
        raise CommandRejected("whitelisted command arrays must contain only non-empty strings")
    if command.cwd is not None:
        raise CommandRejected("whitelisted command cwd must be null in the current phase")
    return command.cmd


def truncate_output(value: str) -> tuple[str, bool]:
    if len(value) <= OUTPUT_MAX_CHARS:
        return value, False
    return value[:OUTPUT_MAX_CHARS], True


def is_sensitive_env_name(name: str) -> bool:
    normalized = name.upper()
    return any(marker in normalized for marker in SENSITIVE_ENV_MARKERS)


def build_command_env(source_env: dict[str, str] | None = None) -> dict[str, str]:
    source = source_env or os.environ
    allowed_names = set(PASSTHROUGH_ENV_NAMES)
    command_env: dict[str, str] = {}
    for name, value in source.items():
        normalized = name.upper()
        if normalized in allowed_names and not is_sensitive_env_name(normalized):
            command_env[name] = value
            if normalized == "PATH":
                command_env.setdefault("PATH", value)
    return command_env


def execute_whitelisted_command(name: str) -> dict[str, Any]:
    tool_name = f"{COMMAND_TOOL_PREFIX}{name}"
    try:
        commands = load_commands()
    except CommandConfigError as error:
        detail = {"tool": tool_name, "reason": str(error)}
        log_tool_call(tool_name, RiskLevel.BLOCKED.value, "rejected", detail)
        raise

    command = commands.get(name)
    if command is None:
        detail = {"tool": tool_name, "reason": "command is not whitelisted"}
        log_event("tool_rejected", detail)
        log_tool_call(tool_name, RiskLevel.BLOCKED.value, "rejected", detail)
        raise CommandNotAllowed(f"command is not whitelisted: {name}")

    try:
        ensure_allowed(command.risk_level)
        command_array = validate_command(command)
    except (PermissionDenied, CommandRejected) as error:
        detail = {"tool": tool_name, "risk_level": command.risk_level.value, "reason": str(error)}
        log_event("tool_rejected", detail)
        log_tool_call(tool_name, command.risk_level.value, "rejected", detail)
        raise

    try:
        completed = subprocess.run(
            command_array,
            cwd=None,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            shell=False,
            check=False,
            env=build_command_env(),
        )
    except Exception as error:
        detail = {"tool": tool_name, "error": type(error).__name__, "message": str(error)}
        log_event("tool_failed", detail)
        log_tool_call(tool_name, command.risk_level.value, "failed", detail)
        raise

    stdout, stdout_truncated = truncate_output(completed.stdout)
    stderr, stderr_truncated = truncate_output(completed.stderr)
    result = {
        "name": name,
        "command": command_array,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }
    status = "success" if completed.returncode == 0 else "failed"
    log_tool_call(
        tool_name,
        command.risk_level.value,
        status,
        {
            "tool": tool_name,
            "returncode": completed.returncode,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
        },
    )
    return result
