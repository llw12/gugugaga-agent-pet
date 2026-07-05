# Gugugaga Agent Pet

Gugugaga Agent Pet is a Windows desktop pet project. The long-term goal is a small, friendly computer assistant, but the current implementation is intentionally narrow and local-first.

## Current Phase

Phase 3: Tauri + React desktop pet frontend connected to a local FastAPI backend with read-only computer status tools.

Implemented now:

- Tauri 2 desktop window configuration: transparent, borderless, always on top.
- React + TypeScript + Vite frontend.
- Per-frame PNG animation for `idle`, `thinking`, `working`, `success`, `warning`, and `sleeping`.
- Debug panel for manually switching pet animation state.
- Chat panel that sends `user_message` events over WebSocket.
- Local FastAPI mock backend with `GET /health` and `WebSocket /ws`.
- Read-only system status endpoints: `GET /api/system/overview` and `GET /api/process/top`.
- Status panel with manual refresh.
- Rule-based mock agent: when the message contains `电脑状态`, `卡`, `CPU`, `内存`, or `磁盘`, the backend reads system overview and top processes, then returns a short summary.
- Frontend pet state changes driven by backend `pet_state` events.
- Offline UI: when the backend is not running, the chat panel shows `Agent 后端未连接`; the pet remains visible and falls back to `idle`.

Not implemented in Phase 3:

- LLM integration
- SQLite storage
- shell command execution
- tool whitelist or approval workflow
- PyInstaller or Tauri sidecar packaging

## Install

Install frontend dependencies:

```powershell
npm --prefix apps/desktop install
```

Install backend dependencies:

```powershell
python -m pip install -e apps/agent-server
```

Running the native Tauri window also requires Rust and Cargo.

## Start Backend

Start the local mock Agent server:

```powershell
npm run dev:agent
```

Equivalent direct command:

```powershell
python -m uvicorn app.main:app --app-dir apps/agent-server --host 127.0.0.1 --port 8765
```

Health check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/health
```

## Start Frontend

Start the Vite frontend:

```powershell
npm run dev:desktop
```

Open:

```text
http://127.0.0.1:1420/
```

Run the native Tauri shell:

```powershell
npm --prefix apps/desktop run tauri dev
```

## Build

```powershell
npm --prefix apps/desktop run build
```

## Phase 2 WebSocket Flow

Frontend sends:

```json
{
  "type": "user_message",
  "payload": {
    "text": "hello"
  }
}
```

Backend mock replies in this order:

```text
pet_state thinking
assistant_message "咕咕嘎嘎收到啦，我正在处理。"
pet_state working
assistant_message "这是 Phase 2 mock 回复，后续会接入电脑状态工具。"
pet_state success
final
```

For status questions, the `working` step calls only read-only psutil APIs and returns a summary of CPU, memory, disk, and top processes.

## HTTP Status APIs

System overview:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/api/system/overview
```

Top processes:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/api/process/top
```

These APIs are read-only. They do not execute shell commands, delete files, kill processes, write registry keys, or modify system state.

## Pet Assets

Animation assets live here:

```text
apps/desktop/src/assets/pet/
  idle/000.png 001.png 002.png 003.png
  thinking/000.png 001.png 002.png 003.png
  working/000.png 001.png 002.png 003.png 004.png 005.png
  success/000.png 001.png 002.png 003.png
  warning/000.png 001.png 002.png 003.png
  sleeping/000.png 001.png 002.png 003.png
```

Rules:

- Each animation state has its own folder.
- Frame names use three-digit ascending numbers such as `000.png`, `001.png`.
- Current frames are treated as square canvases, recommended size `1254x1254`.
- Assets must be true transparent PNGs with real alpha pixels.
- Do not use checkerboard fake transparency; it will render as real pixels on the desktop.

Check alpha transparency:

```powershell
npm run check:alpha
```

## Next Phase

- Add confirmation dialog.
- Add safe tool registry and command whitelist.
- Add SQLite audit logs.
- Add optional LLM provider only after tool permission boundaries exist.
- Plan PyInstaller sidecar packaging for Tauri.
