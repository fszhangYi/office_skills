# PyQt + Web Windows 打包参考

## 目录

```
build/cpython/          # python.org 安装前缀（gitignore）
build/packvenv/         # 只用上面的 python 创建（gitignore）
packaging/<app>.spec
packaging/rthook_dll.py
frontend/dist/          # 或项目已有的静态目录
dist/<App>/             # onedir：<App>.exe 与 _internal/ 或同级 DLL
```

`build/`、`dist/` 放进 `.gitignore`。

## 拒绝 conda

```python
def is_conda_prefix(prefix: str) -> bool:
    text = prefix.lower().replace("/", "\\")
    return "\\miniconda" in text or "\\anaconda" in text or "\\conda\\" in text
```

`build()` 开头若 `is_conda_prefix(sys.base_prefix)` 为真，退出并提示改用官方 Python。

同名 DLL 优先取自 `sys.base_prefix`、`base_prefix/DLLs`、当前环境里 PyQt/PySide 的 Qt `bin`。解析路径在 conda 下、当前前缀不是 conda，则不要收进包。

## onedir spec 骨架

`SPECPATH` 是 spec 所在目录。项目根用 `Path(SPECPATH).resolve().parent`（spec 若在 `packaging/` 下只跳一层）。

```python
from PyInstaller.building.datastruct import TOC

datas = [(str(frontend_dist), "frontend-dist")]
hidden = ["PyQt6.QtWebEngineWidgets", "PyQt6.QtWebEngineCore"]

a = Analysis(
    [str(entry)],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    runtime_hooks=[str(root / "packaging" / "rthook_dll.py")],
    noarchive=False,
)

def _ship(item):
    name = item[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    src = (item[1] if len(item) > 1 else "").replace("\\", "/").lower()
    if name.startswith("api-ms-win-") or name == "ucrtbase.dll":
        return False
    if any(part in src for part in ("miniconda", "anaconda", "/conda/")):
        return False
    return True

a.binaries = TOC([item for item in a.binaries if _ship(item)])
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name=app_name,
    console=False,
    upx=False,
    icon=str(icon_ico),
)
coll = COLLECT(exe, a.binaries, a.datas, name=app_name, upx=False)
```

PySide6 把 hiddenimports 换成 `PySide6.QtWebEngineWidgets`。以入口真实 import 为准，不要两套 Qt 一起打。

额外确认 wheel 的 Qt `bin` 里有 `d3dcompiler_47.dll`。钩子没带走时，用 `binaries=[(path, ".")]` 加进去。不要从 `C:\Windows\System32` 复制 `api-ms-win-*.dll`。

## 运行时钩子

钩子在主脚本之前执行。只做搜索路径和加载失败提示。

```python
import os, sys
from pathlib import Path

if getattr(sys, "frozen", False):
    folder = Path(sys._MEIPASS)
    os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(folder))
    for key in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH"):
        os.environ.pop(key, None)
```

然后对目录里存在的 `VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`、`MSVCP140.dll` 调用 `kernel32.LoadLibraryW(绝对路径)`。失败时解析该 PE 的导入表（导入目录 RVA，按节表换成文件偏移，读 DLL 名）。同目录有这个依赖就先加载它；没有就按名字加载。第一个失败的名字用 `user32.MessageBoxW` 显示，然后 `os._exit(1)`。

## 页面与配置目录

```python
def frontend_index() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend-dist" / "index.html"
    return Path(__file__).resolve().parents[1] / "frontend" / "dist" / "index.html"
```

```python
from PyQt6.QtWebEngineCore import QWebEngineProfile
base = Path(os.environ["LOCALAPPDATA"]) / app_name
profile = QWebEngineProfile.defaultProfile()
profile.setCachePath(str(base / "cache"))
profile.setPersistentStoragePath(str(base / "storage"))
```

## 出包后要搜到的文件

在 `dist/<App>/` 递归查找。Qt6 常见位置在 `_internal/PyQt6/Qt6/`（PySide 为 `PySide6`）。以找到为准，不要写死一层子目录。

| 必须存在 | 必须不存在 |
|---|---|
| `QtWebEngineProcess.exe` | `api-ms-win-*.dll` |
| `platforms/qwindows.dll` | `ucrtbase.dll` |
| `d3dcompiler_47.dll` | `libtommath.dll` |
| `icudtl.dat` | 路径含 Miniconda 的 DLL |
| `qtwebengine_resources.pak` | |
| 前端 `index.html` | |
| `VCRUNTIME140.dll`、`VCRUNTIME140_1.dll` | |

## 干净环境启动

```powershell
$env:PATH = "C:\Windows\System32;C:\Windows"
Remove-Item Env:PYTHONPATH, Env:QT_PLUGIN_PATH, Env:QT_QPA_PLATFORM_PLUGIN_PATH -ErrorAction SilentlyContinue
Get-ChildItem Env:CONDA* | ForEach-Object { Remove-Item "Env:$($_.Name)" }
Start-Process .\dist\<App>\<App>.exe -WorkingDirectory C:\Windows
```

看到主窗口并且本地页面画出来后再交给用户。进程测完要结束掉，避免下次打包因文件占用写不进去。
