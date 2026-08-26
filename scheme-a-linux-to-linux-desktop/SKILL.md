---
name: scheme-a-linux-to-linux-desktop
description: >-
  On Linux, build a self-contained Linux desktop onedir package for Scheme A
  stacks (React+Vite + FastAPI) with PyInstaller: binary + _internal, no Python
  required on the target machine. Use when the user asks for Linux 桌面包,
  PyInstaller onedir, Scheme A Linux package, EOAT-Selector Linux zip, or
  scheme-a-linux-to-linux-desktop after scheme-a-desktop-compat.
---

# Scheme A：Linux → Linux 桌面打包

在 **Linux** 上产出 **无外部依赖** 的 Linux 桌面 onedir（可执行文件 + `_internal/`）。目标机不需要再装 Python/Node/pip。

**前置**：`scheme-a-desktop-compat` 已完成（或项目已有 `desktop_main` / `paths` / native `.spec` / `build_desktop.py`）。

## 何时用

- 用户要 Linux 桌面分发 / AutoDL 上打 Linux 包  
- 栈为方案 A（Vite 前端 + FastAPI 桌面入口）  
- 明确拒绝「目标机再 pip」的便携 Web 包  

## 工作流

```
Task Progress:
- [ ] 1. 确认 compat 层齐全
- [ ] 2. npm ci && npm run build → frontend/dist/index.html
- [ ] 3. backend venv：pip install -r requirements.txt -r requirements-desktop.txt
- [ ] 4. PyInstaller --onedir 使用 packaging/<app>-desktop.spec
- [ ] 5. 舞台到 release/<App>-desktop-linux-x64-<ts>/
- [ ] 6. 写 README.txt + BUILD_INFO.json；打 tar.gz 与 zip
- [ ] 7. 冒烟：./AppName；curl /api/health 与 / → 200
```

首选：

```bash
python3 scripts/build_desktop.py              # 含前端构建
python3 scripts/build_desktop.py --skip-frontend
# 或
bash scripts/build-desktop.sh
```

默认 `--target native`（当前 Linux）。**不要**把本产物拷到 Windows 当 exe 用；Windows 用 `scheme-a-linux-to-windows-desktop`。

## Spec / 构建要点

- `SPECPATH` → `ROOT = Path(SPECPATH).resolve().parent`  
- datas：`frontend/dist` → `frontend-dist`  
- entry：`backend/app/desktop_main.py`，`pathex=[backend]`  
- onedir：`exclude_binaries=True` + `COLLECT`  
- 可用 `collect_all` 收 uvicorn/fastapi 等；体积大可接受  
- 产物名带平台：`linux-x64`（或 `linux-arm64`）  

## 运行时行为（验收时核对）

1. `frozen=True`，数据目录 `~/.local/share/<app-id>/`  
2. 内嵌 uvicorn 监听 `127.0.0.1`  
3. 有 DISPLAY 时尝试 pywebview；无 GTK/`gi` 或无 DISPLAY → **浏览器回退**，主进程不退出  
4. `/api/health` 与 SPA `/` 可用  

冒烟示例：

```bash
cd release/<App>-desktop-linux-x64-<ts>
EOAT_PORT=8030 ./AppName &
sleep 2
curl -s http://127.0.0.1:8030/api/health
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8030/
```

## 常见问题

| 问题 | 处理 |
|---|---|
| 找不到 `frontend/dist` | 先 `npm run build`；检查 spec ROOT |
| webview 因无 `gi` 崩溃 | desktop_main 必须捕获并回退浏览器 |
| 主包 JS >500kB 告警 | 可忽略或后续路由懒加载 |
| 误用旧 `build_release.py`（目标机 pip） | 停用；只认 PyInstaller desktop |

## 验收

- [ ] `release/...-linux-x64-.../AppName` 可执行  
- [ ] `_internal/frontend-dist/index.html` 存在  
- [ ] `BUILD_INFO.json`：`self_contained: true`，`requires_python_on_target: false`  
- [ ] 冒烟 health + index 200  

## 附加资源

- 产物布局与 README 模板：[reference.md](reference.md)
