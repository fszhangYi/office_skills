# Linux → Windows（Scheme A）参考

## 目录约定

```
.tools/win-python/          # embeddable CPython（可 gitignore）
.wine-<app>/                # Wine prefix
packaging/<app>-desktop-win.spec
packaging/run_pyinstaller_wine.py
release/<App>-desktop-windows-x64-<utc>/
  AppName.exe
  _internal/
  README.txt
  BUILD_INFO.json
```

## `run_pyinstaller_wine.py` 核心

```python
import sys
sys._pyi_isolated_subprocess = True
from PyInstaller.__main__ import run
run()
```

可选：在 Wine 的 `PyInstaller/isolated/_parent.py` 末尾覆盖：

```python
def call(function, *args, **kwargs):
    return function(*args, **kwargs)
```

## base_library 注入前缀（最小集）

`pkgutil` `inspect` `copy` `pathlib` `typing` `contextlib` `dataclasses`
`importlib` `json` `logging` `collections` `urllib` `email` `html` `xml`
`encodings` `asyncio` `concurrent` `multiprocessing` `zoneinfo`

## 与 PyQt Wine skill 的区别

| | Scheme A FastAPI 桌面 | PyQt Wine skill |
|---|---|---|
| UI | 内嵌 HTTP + webview/浏览器 | Qt widgets |
| 后处理重点 | stdlib zip | qwindows.dll + Qt plugins |
| numpy | 钉 1.23.5（Wine 6） | 通常非关键 |

## 用户侧说明模板

```text
1. 解压 zip
2. 双击 AppName.exe
3. 无需安装 Python / Node
4. 数据目录：%APPDATA%\<app-id>\
```
