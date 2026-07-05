# 咕咕嘎嘎 Agent 桌宠

咕咕嘎嘎 Agent 桌宠是一个 Windows 桌面桌宠项目，目标是逐步做成一个可爱的电脑管家入口。当前仓库先只实现桌宠前端壳，让角色可以透明置顶显示并播放本地 PNG 帧动画。

## 当前阶段

Phase 1：Tauri 2 + React + TypeScript 桌宠动画壳。

当前已包含：

- Tauri 2 桌面窗口配置：无边框、透明背景、置顶。
- React + TypeScript + Vite 前端。
- idle、thinking、working、success、warning、sleeping 六个动画状态。
- 每帧单独 PNG 渲染，使用 `img` + `object-fit: contain`，不再使用 sprite sheet。
- 调试按钮，可打开状态切换面板。

## 安装依赖

```powershell
npm --prefix apps/desktop install
```

如果要运行 Tauri 原生桌面窗口，还需要安装 Rust 和 Cargo。

## 启动

开发模式仅启动前端页面：

```powershell
npm run dev:desktop
```

构建前端：

```powershell
npm --prefix apps/desktop run build
```

运行 Tauri 桌面窗口：

```powershell
npm --prefix apps/desktop run tauri dev
```

## 素材目录

动画素材放在：

```text
apps/desktop/src/assets/pet/
  idle/000.png 001.png 002.png 003.png
  thinking/000.png 001.png 002.png 003.png
  working/000.png 001.png 002.png 003.png 004.png 005.png
  success/000.png 001.png 002.png 003.png
  warning/000.png 001.png 002.png 003.png
  sleeping/000.png 001.png 002.png 003.png
```

命名规范：

- 每个状态一个文件夹。
- 文件名使用三位数字递增：`000.png`、`001.png`。
- 当前单帧画布按正方形处理，建议保持 `1254x1254`。
- 素材必须是真透明 PNG，即透明区域需要真实 alpha 通道。
- 不要使用棋盘格假透明背景；棋盘格会被当作真实像素显示在桌面上。

可以运行透明通道检查：

```powershell
node scripts/check-alpha.mjs
```

## 当前未实现

以下能力还没有实现，也不应该在 Phase 1 中接入：

- FastAPI Agent 后端
- WebSocket 协议通信
- psutil 系统状态读取
- SQLite 记忆或审计日志
- 工具白名单和命令执行
- LLM 或 OpenAI-compatible provider
- PyInstaller、Tauri sidecar 打包

## 下一阶段计划

- 接入本地 FastAPI + WebSocket mock 后端。
- 增加聊天面板、电脑状态面板和确认弹窗。
- 实现安全工具白名单与人工确认流程。
- 增加 psutil 系统状态读取。
- 增加 SQLite 审计日志。
- 规划 Tauri sidecar 与 PyInstaller 打包流程。
