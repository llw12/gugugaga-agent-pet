你是一个资深全栈工程师。请在当前仓库实现“咕咕嘎嘎 Agent 电脑管家桌宠”的 v0.1 MVP。

项目目标：
实现一个 Windows 桌面桌宠应用，前端使用 Tauri 2 + React + TypeScript，动画使用 PNG sprite sheet；后端使用 Python + FastAPI + WebSocket，提供基础 Agent、系统状态查询、白名单命令执行、安全确认、SQLite 记录能力。

技术栈要求：
- 桌宠前端：Tauri 2 + React + TypeScript + Vite
- 动画：第一版使用 PNG sprite sheet，不做 Live2D
- Agent 后端：Python + FastAPI + WebSocket
- 系统工具：psutil
- 记忆/日志：SQLite
- 模型：先预留 OpenAI-compatible API provider，允许通过 .env 配置；如果没有 API Key，就走 mock agent
- 打包：先保留 Tauri sidecar/PyInstaller 的工程结构和文档，v0.1 开发模式可以让前端连接本地 FastAPI
- 安全：工具白名单 + 人工确认 + 审计日志
- 暂时不要实现真实 pywinauto/UI Automation/Playwright 自动操作，只预留接口和目录

素材说明：
我会把以下 6 张 sprite sheet 放到：
apps/desktop/src/assets/spritesheets/

文件名：
- idle.png
- sleeping.png
- success.png
- thinking.png
- warning.png
- working.png

这 6 张图尺寸都是 2048x682。
其中：
- idle/sleeping/success/thinking/warning：4 帧横向排列
- working：6 帧横向排列
前端不要强制切成单帧文件，先用 CSS background-position 或 canvas 根据 frameIndex 播放整张 sprite sheet。
要求角色显示透明背景区域，不要出现白色窗口底色。

请实现以下目录结构：

gugugaga-agent-pet/
  apps/
    desktop/
      package.json
      index.html
      vite.config.ts
      src/
        main.tsx
        App.tsx
        styles.css
        assets/
          spritesheets/
            idle.png
            sleeping.png
            success.png
            thinking.png
            warning.png
            working.png
        pet/
          animationManifest.ts
          PetSprite.tsx
          petState.ts
        components/
          ChatPanel.tsx
          ChatBubble.tsx
          ConfirmDialog.tsx
          StatusPanel.tsx
          DebugPanel.tsx
        api/
          wsClient.ts
          types.ts
      src-tauri/
        tauri.conf.json
        capabilities/
          default.json
        src/
          main.rs

    agent-server/
      pyproject.toml
      .env.example
      app/
        main.py
        ws.py
        protocol.py
        agent/
          loop.py
          prompts.py
          providers.py
        tools/
          registry.py
          system_info.py
          process.py
          shell.py
          file_ops.py
          browser.py
          windows_ui.py
        security/
          permissions.py
          approval.py
          audit_log.py
        storage/
          db.py
          migrations.py
          memory.py
          settings.py
      config/
        commands.example.json
      tests/
        test_permissions.py
        test_system_info.py
        test_shell_whitelist.py

  scripts/
    dev.ps1
    dev-agent.ps1
    build-agent.ps1

  docs/
    architecture.md
    safety.md
    packaging.md

  README.md
  package.json
  .gitignore

前端功能要求：

1. Tauri 窗口
- 无边框
- 透明背景
- 置顶
- 默认尺寸约 360x360 或适合当前 sprite 的比例
- 支持拖动桌宠窗口
- 右键菜单或简易浮动按钮：
  - 打开聊天
  - 查看电脑状态
  - 调试状态切换
  - 退出
- 如果 Tauri API 暂时不方便完整实现右键菜单，先用 React 自定义右键菜单实现

2. 动画状态
实现以下状态：
- idle
- thinking
- working
- success
- warning
- sleeping

动画配置放在：
apps/desktop/src/pet/animationManifest.ts

示例：
idle: 4 frames, fps 4, loop true
thinking: 4 frames, fps 5, loop true
working: 6 frames, fps 8, loop true
success: 4 frames, fps 6, loop false, next idle
warning: 4 frames, fps 4, loop true
sleeping: 4 frames, fps 2, loop true

实现 PetSprite.tsx：
- props: state
- 根据 state 找到对应 sprite sheet
- 用 requestAnimationFrame 或 setInterval 播放帧
- loop=false 的动画播放完后触发 onComplete
- success 播放完成后自动回到 idle
- 如果后端连接失败，仍然显示 idle，不要白屏

3. 状态机
实现 petState.ts：
- 用户输入消息 -> thinking
- 后端返回 tool_start -> working
- 后端返回 approval_required -> warning
- 后端返回 final/success -> success，然后 idle
- 长时间无交互可以进入 sleeping，先预留，默认 10 分钟

4. 聊天面板
实现 ChatPanel：
- 输入框
- 发送按钮
- 消息列表
- 支持展示用户消息、助手消息、系统提示
- 通过 WebSocket 发送 user_message
- 后端未连接时给出“Agent 后端未启动”的提示

5. 确认弹窗
实现 ConfirmDialog：
- 收到 approval_required 事件时显示
- 展示：
  - tool 名称
  - 风险等级
  - 操作摘要
  - 详细说明
- 按钮：
  - 确认执行
  - 取消
- 点击后通过 WebSocket 发送 approval_result

6. 状态面板
实现 StatusPanel：
- 展示 CPU、内存、磁盘、Top 进程
- 通过 HTTP GET /api/system/overview 和 /api/process/top 获取
- 如果失败，显示友好错误

WebSocket 协议要求：

前端发送：
{
  "type": "user_message",
  "payload": {
    "text": "..."
  }
}

{
  "type": "approval_result",
  "payload": {
    "request_id": "...",
    "approved": true
  }
}

后端发送：
{
  "type": "pet_state",
  "payload": {
    "state": "thinking"
  }
}

{
  "type": "assistant_message",
  "payload": {
    "text": "..."
  }
}

{
  "type": "tool_start",
  "payload": {
    "tool": "system.get_overview"
  }
}

{
  "type": "tool_result",
  "payload": {
    "tool": "system.get_overview",
    "result": {}
  }
}

{
  "type": "approval_required",
  "payload": {
    "request_id": "approve_xxx",
    "title": "需要确认",
    "risk_level": "medium",
    "tool": "shell.run_whitelisted",
    "summary": "将执行白名单命令 docker_ps",
    "detail": "该命令只读取 Docker 容器状态，不会修改系统。"
  }
}

{
  "type": "final",
  "payload": {
    "text": "..."
  }
}

后端功能要求：

1. FastAPI
实现：
- GET /health
- GET /api/system/overview
- GET /api/process/top
- WebSocket /ws

监听：
127.0.0.1:8765

2. system_info.py
使用 psutil 获取：
- cpu_percent
- memory total/available/percent
- disk C:\ total/used/free/percent，如果非 Windows 则用 /
- net io counters

3. process.py
获取 Top 10 进程：
- pid
- name
- cpu_percent
- memory_percent
注意处理 psutil.AccessDenied、NoSuchProcess 异常。

4. shell.py
只能执行白名单命令。
白名单文件：
apps/agent-server/config/commands.example.json

示例内容：
{
  "docker_ps": {
    "cmd": ["docker", "ps"],
    "cwd": null,
    "risk": "low",
    "desc": "查看 Docker 容器状态"
  },
  "git_status_fx_code": {
    "cmd": ["git", "-C", "E:\\workspace\\fx-code", "status"],
    "cwd": null,
    "risk": "low",
    "desc": "查看 fx-code Git 状态"
  },
  "check_node": {
    "cmd": ["node", "-v"],
    "cwd": null,
    "risk": "low",
    "desc": "查看 Node.js 版本"
  },
  "check_npm": {
    "cmd": ["npm", "-v"],
    "cwd": null,
    "risk": "low",
    "desc": "查看 npm 版本"
  },
  "check_java": {
    "cmd": ["java", "-version"],
    "cwd": null,
    "risk": "low",
    "desc": "查看 Java 版本"
  }
}

禁止模型或用户直接传入任意 shell 命令。
shell.run_whitelisted 只接受 command_id。
使用 subprocess.run，设置 timeout，例如 60 秒。
返回 stdout、stderr、exit_code、duration_ms。
不要使用 shell=True。

5. 工具注册
registry.py 中注册：
- system.get_overview
- process.top
- shell.run_whitelisted
- file.open_folder 先预留，可只实现安全打开固定路径
- browser.open_url 先预留，不自动登录不填表
- windows.list_windows 先预留 mock

每个工具包含：
- name
- description
- input_schema
- risk_level
- handler

6. 安全权限
permissions.py：
定义风险等级：
- safe
- low
- medium
- high
- blocked

策略：
- safe / low：允许直接执行
- medium：需要 approval_required
- high：v0.1 先拒绝执行，返回需要未来版本支持
- blocked：拒绝执行

绝对禁止：
- 删除文件
- 格式化磁盘
- 修改注册表
- 杀进程
- 输入密码/验证码
- 支付/下单/转账
- 执行任意 shell 命令

7. 审计日志
SQLite 记录：
- conversations
- tool_calls
- audit_logs
- settings
- memories

实现 storage/db.py：
- 初始化数据库
- 创建表
- 提供简单 insert 方法

audit_log.py：
- log_event(event_type, detail)
- log_tool_call(...)

8. Agent loop
第一版先实现规则 Agent + 可选 LLM。

规则 Agent：
- 如果用户消息包含“电脑状态 / 卡 / CPU / 内存 / 磁盘”，调用 system.get_overview + process.top
- 如果包含“docker”，调用 shell.run_whitelisted command_id=docker_ps
- 如果包含“node”，调用 check_node
- 如果包含“npm”，调用 check_npm
- 如果包含“java”，调用 check_java
- 否则返回普通聊天回复：“咕咕嘎嘎收到啦，目前 v0.1 主要支持电脑状态检查和白名单命令。”

可选 LLM：
- providers.py 预留 OpenAI-compatible client
- 从 .env 读取：
  - LLM_BASE_URL
  - LLM_API_KEY
  - LLM_MODEL
- 如果没有配置，则使用规则 Agent
- 不要让 LLM 直接执行工具，必须经过 Tool Registry 和 Permission Gate

9. approval 机制
当工具 risk_level 为 medium：
- 生成 request_id
- 通过 WebSocket 发 approval_required
- 暂停执行，等待前端 approval_result
- 如果 approved=true，执行工具
- 如果 approved=false，返回“已取消操作”
v0.1 里可以先把 docker_ps/check_node 设为 low，保留 medium 流程用于 npm_build 示例。

10. 测试
Python 测试至少覆盖：
- blocked/high 风险操作不能执行
- shell.run_whitelisted 不接受任意命令
- system overview 返回必要字段
- process top 不因权限异常崩溃

前端至少保证：
- npm run build 能通过
- TypeScript 无明显类型错误

根目录脚本要求：
package.json 提供：
- dev:desktop
- dev:agent
- dev

PowerShell 脚本：
scripts/dev-agent.ps1：
进入 apps/agent-server，安装依赖提示，启动 uvicorn app.main:app --host 127.0.0.1 --port 8765

scripts/dev.ps1：
提示先启动 agent，再启动 desktop，或分别启动两个进程。

README 要写清楚：
- 项目介绍
- 目录结构
- 素材放置位置
- 开发环境要求
- 如何启动后端
- 如何启动桌宠前端
- WebSocket 协议
- 安全设计
- 白名单命令配置
- 后续计划：Live2D、语音、Ollama、pywinauto、Playwright、Tauri sidecar 打包

docs/packaging.md 要写清楚后续打包路线：
- 使用 PyInstaller 将 apps/agent-server 打包为 gugugaga-agent.exe
- 将 exe 作为 Tauri sidecar externalBin
- Tauri 启动时 spawn sidecar
- 前端连接 127.0.0.1:8765
- 退出桌宠时关闭 sidecar

实现约束：
- 不要实现危险电脑操作
- 不要让任何用户输入变成任意 shell 命令
- 不要使用 shell=True
- 不要把 API Key 写死
- 不要提交 node_modules、.venv、dist、target
- 代码要尽量小而清晰，v0.1 优先能跑通
- 每个核心模块加必要注释
- 如果当前仓库已有文件，先检查结构，不要盲目覆盖用户已有代码

完成后请输出：
1. 已创建/修改的文件列表
2. 如何运行
3. 当前支持的功能
4. 尚未实现的功能
5. 重要安全限制