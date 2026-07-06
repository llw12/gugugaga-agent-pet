# Gugugaga Agent Pet

Gugugaga Agent Pet is a Windows desktop pet project. The long-term goal is a small, friendly computer assistant, but the current implementation is intentionally narrow and local-first.

## Current Phase

Phase 4: Tauri + React desktop pet frontend connected to a local FastAPI backend with read-only computer status tools, audit logging, and approval dialog skeletons.

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
- Confirmation dialog skeleton for `approval_required` events.
- Frontend pet state changes driven by backend `pet_state` events.
- Offline UI: when the backend is not running, the chat panel shows `Agent 后端未连接`; the pet remains visible and falls back to `idle`.

Safety framework skeleton prepared:

- Risk levels: `safe`, `low`, `medium`, `high`, `blocked`.
- Read-only tool registry with only `system.get_overview` and `process.top`.
- Permission gate executes only `safe` and `low` tools for now.
- SQLite schema bootstrap for audit logs, tool calls, and settings.
- Tool execution records `success`, `failed`, and `rejected` audit entries.
- Unknown tools are rejected and audited instead of surfacing as raw server errors.
- WebSocket supports `approval_required` and `approval_result` for a simulated medium-risk request.
- Approval requests are tracked in an in-memory pending map with request id, expiry, and handled-state validation.
- The frontend includes a confirmation dialog skeleton for approval events.
- Phase 5 shell whitelist files are present as configuration placeholders only. They are not wired to any execution path.

Not implemented in Phase 4:

- LLM integration
- shell command execution
- medium/high/blocked tool execution
- real approval workflow that executes tools after confirmation
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

## Tests

Install backend dependencies first:

```powershell
python -m pip install -e apps/agent-server
```

Run backend safety tests:

```powershell
python -m pytest apps/agent-server/tests
```

The current tests cover permission gating, read-only tool execution, unknown tool rejection, medium-risk rejection, and approval request state validation. They do not execute shell commands or call any LLM.

## Phase 4 WebSocket Flow

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
assistant_message "电脑状态摘要：CPU ...，内存 ...，磁盘 ...。当前资源占用靠前的进程有：..."
pet_state success
final
```

For status questions, the `working` step calls only read-only psutil APIs through the safe tool registry and returns a summary of CPU, memory, disk, and top processes. For normal chat, the backend returns a mock hint asking the user to try a computer status question or the approval demo.

For confirmation testing, send a chat message containing `确认`, `approval`, or `medium`. The backend sends `approval_required` for a simulated `mock.medium_approval` tool. The frontend shows a confirmation dialog and sends `approval_result`, but the backend only records the result and does not execute any medium-risk tool.

Approval results are validated before being accepted:

- unknown request ids are rejected and audited
- expired request ids are rejected and audited
- already handled request ids are rejected and audited
- accepted results are audited with `executed: false`

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

## Safety Rules

The current backend only registers two read-only tools:

- `system.get_overview` with `safe` risk
- `process.top` with `low` risk

The registry also contains `mock.medium_approval` only to demonstrate approval UI. The permission layer refuses `medium`, `high`, and `blocked` tools for now. There is still no LLM integration, arbitrary shell execution, file deletion, process killing, registry editing, payment flow, password input, or UI automation.

## Phase 5 Whitelist Placeholder

The repository includes a placeholder whitelist configuration at:

```text
apps/agent-server/config/commands.example.json
```

This file documents the future shape of whitelisted commands. The backend does not load it or execute anything from it yet. There is still no shell execution path in the application.

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

- Persist approval state if needed beyond in-memory demo sessions.
- Add command whitelist execution only after approval flow and tests exist.
- Add optional LLM provider only after tool permission boundaries exist.
- Plan PyInstaller sidecar packaging for Tauri.
