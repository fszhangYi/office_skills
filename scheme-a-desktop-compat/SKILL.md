---
name: scheme-a-desktop-compat
description: >-
  Validate whether a project matches 技术路线 Scheme A (React+Vite+TS frontend,
  Python FastAPI backend, Agent/SSE tools, optional Tauri) and, if compliant,
  add cross-platform desktop packaging compatibility code (frozen paths,
  desktop entry, PyInstaller specs, build scripts). Use when the user mentions
  方案A, 技术路线A, Scheme A, 跨平台打包兼容, desktop packaging prep, or asks to
  check EOAT-style stack readiness for PyInstaller desktop builds.
---

# Scheme A 校验 + 桌面打包兼容代码

对照「方案 A」技术栈检查当前仓库；**仅在符合时**向项目写入跨平台桌面打包所需兼容层。参考实现：`eoat-selector`（React+Vite+Ant Design + FastAPI + SSE Agent；桌面暂用 PyInstaller，Tauri 可选）。

## 方案 A 判定标准（必须全部满足「核心」）

| 层 | 核心信号（至少一项） | 可选增强 |
|---|---|---|
| 前端 | `frontend/` 含 Vite + React + TypeScript（`package.json` 有 `vite`/`react`） | Ant Design / shadcn |
| 后端 | `backend/`（或等价）含 FastAPI `app`、`uvicorn`、`requirements.txt` | SQLAlchemy / aiosqlite |
| Agent | SSE 或工具编排 API（如 `/api/agent`、LangGraph/工具调用） | OpenAI 兼容 Key |
| 桌面目标 | 同一套前端 + 本地后端；密钥不下发客户端 | Tauri 2 说明或后续接入 |
| 数据 | SQLite 可运行 MVP，或 Postgres+pgvector 可切换 | seed / 规则引擎 |

**不符合方案 A**：输出差距清单后停止，**不要**强行加 PyInstaller 桌面脚手架。典型反例：纯 Next.js/Nest（方案 B）、Vue+Spring/Go 主后端（方案 C）。

## 工作流

```
Task Progress:
- [ ] 1. 扫描仓库结构与依赖，对照上表打分
- [ ] 2. 向用户报告：符合 / 部分符合 / 不符合（附证据路径）
- [ ] 3. 仅「符合」或用户确认「按 A 补齐」后，写入兼容代码
- [ ] 4. 更新 .gitignore（release/、packaging/dist*、.tools/、.wine-*）
- [ ] 5. 冒烟：frontend build + import desktop entry（开发态）
```

## 符合后必须落地的兼容代码

按项目实际包名替换 `app` / `frontend` 路径；产物名用产品名而非写死 EOAT。

### 1. Frozen 路径与可写数据目录

新增 `backend/app/paths.py`（或等价）：

- `is_frozen()` → `sys.frozen` + `_MEIPASS`
- `resolve_frontend_dist()` → `FRONTEND_DIST` / `_MEIPASS/frontend-dist` / `frontend/dist`
- `user_data_dir()` → Linux `~/.local/share/<app>/`，macOS Application Support，Windows `%APPDATA%\<app>\`
- `ensure_runtime_env()` → 设置 `FRONTEND_DIST`、`DATABASE_URL`（绝对路径 SQLite），`chdir` 到用户数据目录

**禁止**把 SQLite 写进只读的 PyInstaller `_MEIPASS`。

### 2. FastAPI 托管前端 SPA

在应用入口（如 `main.py`）：

- 启动时解析 `frontend-dist`
- `mount("/assets", ...)`
- SPA fallback 返回 `index.html`（勿吞 `/api/*`）

### 3. 桌面入口

新增 `backend/app/desktop_main.py`：

1. 先 `ensure_runtime_env()`，再导入 `Settings` / 重建 DB engine  
2. 后台线程跑 `uvicorn`（`127.0.0.1` + 随机端口或 `EOAT_PORT`）  
3. 等 `/api/health`  
4. 优先 `pywebview` 原生窗；无 DISPLAY / 无 GTK/Qt/WebView2 时 **回退系统浏览器**，进程保持运行，**禁止**因 webview 失败直接退出  

### 4. 打包脚手架（不在本 skill 内执行完整 Wine 构建）

创建并保持可运行：

| 路径 | 作用 |
|---|---|
| `packaging/<app>-desktop.spec` | Linux/macOS native PyInstaller onedir |
| `packaging/<app>-desktop-win.spec` | Windows / Wine 用精简 hiddenimports（少用 `collect_all`） |
| `packaging/run_pyinstaller_wine.py` | 设置 `sys._pyi_isolated_subprocess=True` 规避 Wine 隔离子进程崩溃 |
| `scripts/eoat_platform.py` 或 `platform_detect.py` | `linux-x64` / `windows-x64` 等 slug |
| `scripts/build_desktop.py` | `--target native|windows`，产物进 `release/` |
| `scripts/build-desktop.sh` / `.bat` | 薄封装 |
| `backend/requirements-desktop.txt` | `pyinstaller`、`pywebview` |

`SPECPATH` 在 PyInstaller 里是 **spec 所在目录**：`ROOT = Path(SPECPATH).resolve().parent`（不要多跳一级）。

### 5. 明确反模式（写入文档/注释）

- ❌ 把 Linux `.venv` 打进包指望 Windows 能跑  
- ❌ 「便携 Web 包」要求目标机再装 Python / 首次 pip（不算无依赖桌面端）  
- ❌ 仅 `npm run build` 而无后端嵌入  

## 完成后告知用户

- 判定结果与证据  
- 新增/修改文件列表  
- 下一步：用 `scheme-a-linux-to-linux-desktop` 或 `scheme-a-linux-to-windows-desktop` 真正出包  

## 附加资源

- 判定细则与文件模板要点：[reference.md](reference.md)
