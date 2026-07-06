import asyncio
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.security.audit_log import log_event
from app.tools.registry import execute_tool

app = FastAPI(title="Gugugaga Agent Mock Server", version="0.4.0")
APPROVAL_TTL_SECONDS = 300


@dataclass
class PendingApproval:
    request_id: str
    tool: str
    risk_level: str
    created_at: float
    expires_at: float
    handled: bool = False


pending_approvals: dict[str, PendingApproval] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1420", "http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "phase": "4"}


@app.get("/api/system/overview")
async def system_overview() -> dict[str, Any]:
    return await asyncio.to_thread(execute_tool, "system.get_overview")


@app.get("/api/process/top")
async def process_top() -> dict[str, list[dict[str, Any]]]:
    processes = await asyncio.to_thread(execute_tool, "process.top")
    return {"processes": processes}


async def send_event(websocket: WebSocket, event_type: str, payload: dict[str, Any] | None = None) -> None:
    await websocket.send_json({"type": event_type, "payload": payload or {}})


def purge_expired_approvals(now: float | None = None) -> None:
    current = now or time.time()
    expired_ids = [
        request_id
        for request_id, approval in pending_approvals.items()
        if approval.handled or approval.expires_at < current
    ]
    for request_id in expired_ids:
        pending_approvals.pop(request_id, None)


def create_pending_approval(tool: str, risk_level: str) -> PendingApproval:
    now = time.time()
    purge_expired_approvals(now)
    request_id = f"approval_{uuid4().hex}"
    approval = PendingApproval(
        request_id=request_id,
        tool=tool,
        risk_level=risk_level,
        created_at=now,
        expires_at=now + APPROVAL_TTL_SECONDS,
    )
    pending_approvals[request_id] = approval
    return approval


def record_approval_result(request_id: str, approved: bool) -> tuple[bool, str]:
    approval = pending_approvals.get(request_id)
    if approval is None:
        log_event("approval_result_rejected", {"request_id": request_id, "reason": "unknown_request"})
        return False, "确认请求不存在或已过期。"
    if approval.handled:
        log_event("approval_result_rejected", {"request_id": request_id, "reason": "already_handled"})
        return False, "确认请求已经处理过。"
    if approval.expires_at < time.time():
        approval.handled = True
        log_event("approval_result_rejected", {"request_id": request_id, "reason": "expired"})
        pending_approvals.pop(request_id, None)
        return False, "确认请求已过期。"

    approval.handled = True
    log_event(
        "approval_result",
        {
            "request_id": request_id,
            "approved": approved,
            "tool": approval.tool,
            "risk_level": approval.risk_level,
            "executed": False,
        },
    )
    return True, "已记录确认结果。Phase 4 当前不会执行 medium/high/blocked 工具。"


def should_query_system(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in ["电脑状态", "卡", "cpu", "内存", "磁盘"])


def should_request_approval(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in ["确认", "approval", "medium"])


def build_system_summary(overview: dict[str, Any], processes: list[dict[str, Any]]) -> str:
    memory = overview["memory"]
    disk = overview["disk"]
    top_names = "、".join(process["name"] for process in processes[:3]) or "暂无"
    return (
        f"电脑状态摘要：CPU {overview['cpu_percent']}%，"
        f"内存 {memory['percent']}%，磁盘 {disk['percent']}%。"
        f"当前资源占用靠前的进程有：{top_names}。"
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            message_type = message.get("type")
            if message_type == "approval_result":
                payload = message.get("payload", {})
                approved = bool(payload.get("approved"))
                request_id = str(payload.get("request_id", ""))
                accepted, result_message = await asyncio.to_thread(record_approval_result, request_id, approved)
                await send_event(websocket, "pet_state", {"state": "idle"})
                await send_event(
                    websocket,
                    "assistant_message",
                    {"text": result_message},
                )
                final_text = "审批演示流程结束，未执行任何风险工具。" if accepted else "审批结果未被接受，未执行任何风险工具。"
                await send_event(websocket, "final", {"text": final_text})
                continue

            if message_type != "user_message":
                await send_event(websocket, "assistant_message", {"text": "Phase 4 mock 只处理 user_message 和 approval_result。"})
                continue

            text = str(message.get("payload", {}).get("text", ""))
            await send_event(websocket, "pet_state", {"state": "thinking"})
            await asyncio.sleep(0.25)
            await send_event(websocket, "assistant_message", {"text": "咕咕嘎嘎收到啦，我正在处理。"})
            await asyncio.sleep(0.35)
            await send_event(websocket, "pet_state", {"state": "working"})
            await asyncio.sleep(0.45)

            if should_request_approval(text):
                approval = create_pending_approval("mock.medium_approval", "medium")
                await asyncio.to_thread(
                    log_event,
                    "approval_required",
                    {
                        "request_id": approval.request_id,
                        "tool": approval.tool,
                        "risk_level": approval.risk_level,
                        "expires_at": approval.expires_at,
                    },
                )
                await send_event(websocket, "pet_state", {"state": "warning"})
                await send_event(
                    websocket,
                    "approval_required",
                    {
                        "request_id": approval.request_id,
                        "title": "需要确认",
                        "risk_level": approval.risk_level,
                        "tool": approval.tool,
                        "summary": "这是 Phase 4 的 medium 风险工具审批演示。",
                        "detail": "无论你点击取消还是记录确认，当前阶段都只记录审计日志，不会执行任何 medium/high/blocked 工具。",
                    },
                )
                await send_event(websocket, "assistant_message", {"text": "我发起了一个模拟确认请求，但不会执行风险工具。"})
                continue
            elif should_query_system(text):
                overview, processes = await asyncio.gather(
                    asyncio.to_thread(execute_tool, "system.get_overview"),
                    asyncio.to_thread(execute_tool, "process.top"),
                )
                await send_event(websocket, "assistant_message", {"text": build_system_summary(overview, processes)})
            else:
                await send_event(
                    websocket,
                    "assistant_message",
                    {"text": "这是普通 mock 回复。你可以问我电脑状态、CPU、内存、磁盘，或发送“确认”测试审批弹窗。"},
                )

            await asyncio.sleep(0.25)
            await send_event(websocket, "pet_state", {"state": "success"})
            await asyncio.sleep(0.1)
            await send_event(websocket, "final", {"text": "Phase 4 mock 流程完成。"})
    except WebSocketDisconnect:
        return
