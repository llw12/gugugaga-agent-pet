import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.security.audit_log import log_event
from app.tools.registry import execute_tool

app = FastAPI(title="Gugugaga Agent Mock Server", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1420", "http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "phase": "3"}


@app.get("/api/system/overview")
async def system_overview() -> dict[str, Any]:
    return await asyncio.to_thread(execute_tool, "system.get_overview")


@app.get("/api/process/top")
async def process_top() -> dict[str, list[dict[str, Any]]]:
    processes = await asyncio.to_thread(execute_tool, "process.top")
    return {"processes": processes}


async def send_event(websocket: WebSocket, event_type: str, payload: dict[str, Any] | None = None) -> None:
    await websocket.send_json({"type": event_type, "payload": payload or {}})


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
                await asyncio.to_thread(
                    log_event,
                    "approval_result",
                    {"request_id": request_id, "approved": approved, "executed": False},
                )
                await send_event(websocket, "pet_state", {"state": "idle"})
                await send_event(
                    websocket,
                    "assistant_message",
                    {"text": "已记录确认结果。Phase 4 当前不会执行 medium/high/blocked 工具。"},
                )
                await send_event(websocket, "final", {"text": "审批演示流程结束，未执行任何风险工具。"})
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
                request_id = "mock_medium_approval"
                await asyncio.to_thread(
                    log_event,
                    "approval_required",
                    {"request_id": request_id, "tool": "mock.medium_approval", "risk_level": "medium"},
                )
                await send_event(websocket, "pet_state", {"state": "warning"})
                await send_event(
                    websocket,
                    "approval_required",
                    {
                        "request_id": request_id,
                        "title": "需要确认",
                        "risk_level": "medium",
                        "tool": "mock.medium_approval",
                        "summary": "这是 Phase 4 的 medium 风险工具审批演示。",
                        "detail": "无论你点击确认还是取消，当前阶段都只记录审计日志，不会执行任何 medium/high/blocked 工具。",
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
                    {"text": "这是 Phase 3 mock 回复。你可以问我电脑状态、CPU、内存或磁盘。"},
                )

            await asyncio.sleep(0.25)
            await send_event(websocket, "pet_state", {"state": "success"})
            await asyncio.sleep(0.1)
            await send_event(websocket, "final", {"text": "Phase 3 mock 流程完成。"})
    except WebSocketDisconnect:
        return
