import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import psutil

from app.security.permissions import RiskLevel, ensure_allowed
from app.security.audit_log import log_event, log_tool_call

ToolHandler = Callable[[], Any]


class ToolNotFound(RuntimeError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    risk_level: RiskLevel
    handler: ToolHandler


def get_disk_path() -> str:
    if os.name == "nt" and os.path.exists("C:\\"):
        return "C:\\"
    return "/"


def get_system_overview() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    disk_path = get_disk_path()
    disk = psutil.disk_usage(disk_path)
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
        },
        "disk": {
            "path": disk_path,
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        },
    }


def get_top_processes(limit: int = 10) -> list[dict[str, Any]]:
    candidates: list[psutil.Process] = []
    for process in psutil.process_iter(["pid", "name", "memory_percent"]):
        try:
            name = process.info.get("name") or ""
            if process.pid == 0 or name.lower() == "system idle process":
                continue
            process.cpu_percent(interval=None)
            candidates.append(process)
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    time.sleep(0.2)

    processes: list[dict[str, Any]] = []
    for process in candidates:
        try:
            info = process.as_dict(attrs=["pid", "name", "memory_percent"])
            processes.append(
                {
                    "pid": info.get("pid", process.pid),
                    "name": info.get("name") or "unknown",
                    "cpu_percent": round(float(process.cpu_percent(interval=None)), 1),
                    "memory_percent": round(float(info.get("memory_percent") or 0), 2),
                }
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda item: (item["cpu_percent"], item["memory_percent"]), reverse=True)
    return processes[:limit]


TOOLS: dict[str, ToolDefinition] = {
    "system.get_overview": ToolDefinition(
        name="system.get_overview",
        description="Read CPU, memory, and disk usage.",
        risk_level=RiskLevel.SAFE,
        handler=get_system_overview,
    ),
    "process.top": ToolDefinition(
        name="process.top",
        description="Read the top processes by CPU and memory usage.",
        risk_level=RiskLevel.LOW,
        handler=get_top_processes,
    ),
    "mock.medium_approval": ToolDefinition(
        name="mock.medium_approval",
        description="Demonstrate an approval-required medium risk tool. It must not execute in Phase 4.",
        risk_level=RiskLevel.MEDIUM,
        handler=lambda: {"status": "not_executable"},
    ),
}


def execute_tool(name: str) -> Any:
    tool = TOOLS.get(name)
    if tool is None:
        detail = {"tool": name, "reason": "unknown tool"}
        log_event("tool_rejected", detail)
        log_tool_call(name, RiskLevel.BLOCKED.value, "rejected", detail)
        raise ToolNotFound(f"unknown tool: {name}")

    try:
        ensure_allowed(tool.risk_level)
    except Exception as error:
        detail = {"tool": name, "reason": str(error)}
        log_event("tool_rejected", detail)
        log_tool_call(name, tool.risk_level.value, "rejected", detail)
        raise

    try:
        result = tool.handler()
    except Exception as error:
        detail = {"tool": name, "error": type(error).__name__, "message": str(error)}
        log_event("tool_failed", detail)
        log_tool_call(name, tool.risk_level.value, "failed", detail)
        raise

    log_tool_call(name, tool.risk_level.value, "success", {"tool": name})
    return result
