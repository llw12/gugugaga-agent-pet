import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gugugaga Agent Mock Server", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:1420", "http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "phase": "2"}


async def send_event(websocket: WebSocket, event_type: str, payload: dict[str, Any] | None = None) -> None:
    await websocket.send_json({"type": event_type, "payload": payload or {}})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") != "user_message":
                await send_event(websocket, "assistant_message", {"text": "Phase 2 mock 只处理 user_message。"})
                continue

            await send_event(websocket, "pet_state", {"state": "thinking"})
            await asyncio.sleep(0.25)
            await send_event(websocket, "assistant_message", {"text": "咕咕嘎嘎收到啦，我正在处理。"})
            await asyncio.sleep(0.35)
            await send_event(websocket, "pet_state", {"state": "working"})
            await asyncio.sleep(0.45)
            await send_event(
                websocket,
                "assistant_message",
                {"text": "这是 Phase 2 mock 回复，后续会接入电脑状态工具。"},
            )
            await asyncio.sleep(0.25)
            await send_event(websocket, "pet_state", {"state": "success"})
            await asyncio.sleep(0.1)
            await send_event(websocket, "final", {"text": "Phase 2 mock 流程完成。"})
    except WebSocketDisconnect:
        return
