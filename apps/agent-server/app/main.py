import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
            if message.get("type") != "user_message":
                await send_event(websocket, "assistant_message", {"text": "Phase 2 mock 只处理 user_message。"})
                continue

            text = str(message.get("payload", {}).get("text", ""))
            await send_event(websocket, "pet_state", {"state": "thinking"})
            await asyncio.sleep(0.25)
            await send_event(websocket, "assistant_message", {"text": "咕咕嘎嘎收到啦，我正在处理。"})
            await asyncio.sleep(0.35)
            await send_event(websocket, "pet_state", {"state": "working"})
            await asyncio.sleep(0.45)

            if should_query_system(text):
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
