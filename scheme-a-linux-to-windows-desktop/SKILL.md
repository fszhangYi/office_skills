---
name: scheme-a-linux-to-windows-desktop
description: >-
  From a Linux host (e.g. AutoDL), cross-build a self-contained Windows desktop
  onedir package (.exe + _internal) for Scheme A stacks (React+Vite frontend +
  FastAPI backend) via Wine + embeddable CPython + PyInstaller. Use when the user
  asks for Windows 桌面包, Linux 打 Windows, Wine PyInstaller, EOAT Windows zip,
  or scheme-a-linux-to-windows-desktop after scheme-a-desktop-compat.
---

# Scheme A：Linux → Windows 桌面交叉打包

在 **Linux** 上产出 **无外部依赖** 的 Windows 桌面 onedir（`EOAT-Selector.exe` 或项目名 + `_internal/`）。目标机不需要 Python/Node。

**前置**：项目已通过 `scheme-a-desktop-compat`（或已具备等价的 `desktop_main` / paths / win.spec / `build_desktop.py`）。若未通过，先跑兼容 skill。

## 何时用 / 何时不用

| 用 | 不用 |
|---|---|
| 主机是 Linux，要 `.exe` 分发包 | 已有 Windows 构建机 → 优先本机 `build-desktop.bat` |
| Scheme A：Vite 前端 + FastAPI 桌面入口 | PyQt/PySide GUI → 用 `pyqt-windows-crossbuild-wine` |
| 用户明确要「双击即用」 | 只要静态前端或仍依赖目标机 pip 的 Web 包 |

## 工作流

```
Task Progress:
- [ ] 1. 确认 compat 层与 frontend/dist（或先 npm run build）
- [ ] 2. 确认 wine/wine64；建议 winetricks vcrun2019
- [ ] 3. 准备 .tools/win-python 嵌入式 CPython 3.10 + import site + Lib\site-packages
- [ ] 4. Wine pip 安装 requirements + requirements-desktop（清华源）
- [ ] 5. 强制 numpy==1.23.5（Wine 6 无 fetestexcept，numpy 2.x 会崩）
- [ ] 6. 用 run_pyinstaller_wine.py 跑 win.spec（禁用隔离子进程）
- [ ] 7. 后处理：复制 python310.zip、修补 base_library.zip
- [ ] 8. 拷入 release/<App>-desktop-windows-x64-<ts>/ 并打 zip
- [ ] 9. 核对：存在 .exe、_internal/、BUILD_INFO.json、README.txt
```

首选命令（项目已有脚本时）：

```bash
python3 scripts/build_desktop.py --skip-frontend --target windows
# 或
bash scripts/build-desktop.sh --target windows
```

PIP：`PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`（AutoDL 上少用会拖慢官方源的 network_turbo）。

## 规范流水线（无现成脚本时按此实现）

1. **Wine prefix**：项目内 `.wine-<app>/`，`WINEARCH=win64`，`WINEDEBUG=-all`，优先 `wine64`  
2. **Embeddable CPython** `3.10.x-amd64` → `.tools/win-python/`  
3. `python*._pth`：启用 `import site`，并加入 `Lib\site-packages`  
4. `get-pip.py` → `wine64 python.exe get-pip.py -i <mirror>`  
5. `pip install -r backend/requirements.txt -r backend/requirements-desktop.txt`  
6. `pip install numpy==1.23.5`（覆盖）  
7. 路径用 `Z:\...`（Linux `/root/...` → `Z:\root\...`）  
8. 启动：`wine64 python.exe packaging/run_pyinstaller_wine.py ... packaging/<app>-desktop-win.spec`  
9. dist/work 用短路径（如 `/tmp/<app>-dist-win`）减少 Wine 路径问题  
10. **后处理**：`python310.zip` → `_internal/`；把 stdlib 关键模块打进 `base_library.zip`（`pkgutil`/`inspect`/`importlib`/…）  

## 必知故障（来自实测）

| 症状 | 原因 | 处理 |
|---|---|---|
| `SubprocessDiedError: discover_hook_directories` | Wine 杀 PyInstaller 隔离进程 | `run_pyinstaller_wine.py` 设 `_pyi_isolated_subprocess`；或补丁 `isolated.call` 进程内执行 |
| `unimplemented ... fetestexcept` | Wine 6 + 新 UCRT / numpy 2 | `numpy==1.23.5` + `winetricks vcrun2019` |
| `No module named 'pkgutil'` 运行时 | 瘦 `base_library.zip` | 从 embed `python310.zip` 注入 |
| SPECPATH 找不到 `frontend/dist` | ROOT 多 `.parent` 一次 | `ROOT = Path(SPECPATH).resolve().parent` |
| sha256 mismatch vcrun | 缓存损坏 | 删 `~/.cache/winetricks/vcrun2019/` 重装 |

## 验收

- [ ] `release/...-windows-x64-.../AppName.exe` 存在  
- [ ] `_internal/frontend-dist/index.html` 存在  
- [ ] zip 可解压；文档写明「无需安装 Python」  
- [ ] `BUILD_INFO.json`：`self_contained: true`，`platform: windows-x64`  

无法在 Linux 上双击验证 `.exe` 时：至少确认目录结构与体积合理，并提示用户在 Windows 真机试跑。

## 附加资源

- 路径/补丁细节：[reference.md](reference.md)
