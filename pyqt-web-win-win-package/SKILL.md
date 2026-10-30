---
name: pyqt-web-win-win-package
description: >-
  Package a PyQt or PySide plus embedded web app (Qt WebEngine or a local
  frontend) on a Windows build machine into a self-contained program that runs
  on a clean Windows PC with no Python, Node, Qt, or Miniconda. Prefer one exe
  with no _internal folder, an app icon, and a timestamp in the filename. If
  one file cannot work, zip the folder and put the timestamp on the zip. Use
  when the user asks to package PyQt+web, PySide WebEngine, Windows 新电脑无依赖,
  DLL load failed 找不到指定的模块, single exe, timestamp, or
  pyqt-web-win-win-package. This is Windows-to-Windows, not Wine.
---

# PyQt + Web：Windows 本机打成新机器可运行的包

在 **Windows 构建机** 上优先产出 **单个 exe**。交付物里不要出现 `_internal`。做不成单文件时，再把目录压成 zip，时间戳打在 zip 上。把交付物拷到另一台 Windows，双击即可。对方不装 Python、Node、Qt、Anaconda、VC 红发包。

不要走 Wine 交叉打包（那是 `scheme-a-linux-to-windows-desktop`）。本 skill 是 Windows → Windows。

## 何时用

| 用 | 不用 |
|---|---|
| PyQt5/6 或 PySide2/6，界面是内嵌网页 | 纯 FastAPI + pywebview 的方案 A → `scheme-a-linux-to-windows-desktop` |
| 构建机和目标机都是 Windows x64 | 人在 Linux 上打 Windows 包 |
| 目标机不能再装运行环境 | 对方可以自己 `pip install` |

网页壳默认用 **Qt WebEngine**（Chromium 打进目录）。若代码用的是 WebView2，改打 WebEngine，或把 Fixed Version 运行库放进同一目录。不要让用户去装 Evergreen。

## 工作流

```
Task Progress:
- [ ] 1. 用 python.org 官方 CPython 建打包 venv，拒绝 Miniconda
- [ ] 2. 前端先构建，PyPI 安装 PyQt/PySide 与 PyInstaller
- [ ] 3. 先尽力打成单个 exe，不要出现 _internal；单文件时核对外部资源路径
- [ ] 4. 给桌面端选一个合适的图标，写进 spec
- [ ] 5. 运行时钩子在 import Qt 之前按绝对路径加载 DLL；过滤 api-ms-win / ucrtbase / conda 路径，upx=False
- [ ] 6. 冻结路径读网页；缓存写到 LOCALAPPDATA
- [ ] 7. 换一个工作目录、只用 System32 的 PATH 启动，确认页面画出来
- [ ] 8. 单文件成功：exe 文件名带本地时间戳。做不成：压成 zip，时间戳打在 zip 上
```

### 1. 解释器

官方安装包装到项目内 `build/cpython`（`InstallAllUsers=0`，`PrependPath=0`，不要进系统 PATH）。再用它创建 `build/packvenv`。打包脚本只调用 `build/packvenv/Scripts/python.exe`。

`sys.base_prefix` 含 `\miniconda`、`\anaconda` 或 `\conda\` 时 **直接退出**。Miniconda 的 Qt/运行库会在没装 Miniconda 的电脑上报 `DLL load failed` / `找不到指定的模块`（Windows 错误 126）。

构建机 PATH 上就算有 conda，依赖解析也要改用当前前缀里的同名 DLL（`base_prefix`、`DLLs`、wheel 里的 Qt `bin`）。解析结果落在 conda 目录、而当前前缀不是 conda 时，丢掉这个 DLL。

### 2. 依赖与前端

- 先 `npm run build`（或项目等价命令），得到静态目录。
- `pip install` 使用 PyPI 上的 PyQt/PySide **wheel**，不要用 conda-forge 的 Qt。
- 入口或 `hiddenimports` 必须包含实际用到的模块，例如 `PyQt6.QtWebEngineWidgets`。没被分析到的 WebEngine 不会把 `QtWebEngineProcess.exe` 打进去。

### 3. 打包形态

先尽力打成 **单个 exe**（onefile：`exclude_binaries=False`，不要 `COLLECT`）。交付目录里不要出现 `_internal`。

单文件时，数据文件在运行时解压到 `sys._MEIPASS`，不在 exe 旁边。检查每一处外部资源引用：

- 页面、`.pak`、`icudtl.dat` 以及其它打进去的文件都从 `Path(sys._MEIPASS)` 读。不要用 `Path(sys.executable).parent`，也不要留开发时的相对路径。
- spec 里 `datas` 的目标目录名要和代码里的子路径一致。
- 换一个工作目录再启动这个 exe。只在仓库目录里双击通过，不能说明路径是对的。

WebEngine 的子进程经常要求 `QtWebEngineProcess.exe`、`.pak`、`icudtl.dat` 是磁盘上的真文件。单文件打开后若网页空白或子进程退出，不要交付这个 exe。

做不成单文件时：

- 改 onedir，并设 `contents_directory='.'`，让 DLL 和 exe 放在一起。不要使用默认的 `_internal`。
- 把该目录打成 zip。交给用户的是 zip，不是散开的目录。
- 时间戳打在 **zip 文件名**上，例如 `应用名-20261030-101300.zip`。

做成单文件时，时间戳打在 **exe 文件名**上，例如 `应用名-20261030-101300.exe`。时间取打包当时的本地时间，格式 `YYYYMMDD-HHMMSS`。不要覆盖一个不带时间的固定文件名；正在运行的旧 exe 会让覆盖失败，对方拿到的仍是旧包。

给桌面端选一个和这个程序相称的图标，不要留 PyInstaller 默认图标，也不要拿另一个项目的图标来充。图标做法用 `add-favicon`：多尺寸 `.ico`（至少 16、32、48、256），spec 里写 `icon=`。窗口图标和 exe 图标用同一份。

spec 里对 `a.binaries` 过滤：

- 文件名以 `api-ms-win-` 开头，或名为 `ucrtbase.dll`
- 源路径含 `miniconda`、`anaconda`、`\conda\`

`upx=False`。Qt DLL 被 UPX 压过之后会在新电脑上加载失败。

模板见 [reference.md](reference.md)。

### 4. 启动前加载 DLL

Python 3.8+ 加载扩展时用 `LoadLibraryEx`，**忽略** `SetDllDirectory` 和 PATH。运行时钩子要在 `import PyQt` / `PySide` 之前：

1. `os.add_dll_directory(sys._MEIPASS)`，并把该目录加到 PATH 最前。
2. 清掉指向构建机的 `QT_PLUGIN_PATH`、`QT_QPA_PLATFORM_PLUGIN_PATH`、`CONDA_*`、`PYTHONPATH`。
3. 按绝对路径 `LoadLibraryW`：`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`、`MSVCP140.dll`（存在才加载），再加载 Qt 核心 DLL。失败时用 PE 导入表找出第一个缺失的 DLL 名，`MessageBoxW` 后 `os._exit(1)`。无控制台的程序否则只会闪退。

PyInstaller 自带的 PyQt/PySide 运行时钩子负责插件目录和 WebEngine 进程路径。自定义钩子排在它前面，只处理搜索路径和失败提示，不要覆盖它设好的 `QTWEBENGINEPROCESS_PATH`。

### 5. 程序里的路径

- 页面：`Path(sys._MEIPASS) / "<前端目录>" / "index.html"`，用 `QUrl.fromLocalFile`。开发态仍读源码树里的 `dist`。单文件和 onedir 都走 `_MEIPASS`，不要为单文件再写一套“exe 同目录”的路径。
- `QWebEngineProfile` 的 cache 和 persistent storage 指到 `%LOCALAPPDATA%\<app>\`。不要写进解压目录或 zip 里的程序目录（可能只读）。

### 6. 验收（本机窗口打开不算数）

单文件没有可翻的目录，验收靠换目录启动，并确认页面画出来。若退回 onedir，在 **打 zip 之前的目录** 上检查，不要只在构建日志里找字符串。下面这份清单只用于 onedir。

必须有（名字以 wheel 实际布局为准，用递归查找）：

- `QtWebEngineProcess.exe`
- `platforms/qwindows.dll`
- `d3dcompiler_47.dll`
- `icudtl.dat`
- `qtwebengine_resources.pak`
- 前端 `index.html`
- `VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`

必须没有：

- `api-ms-win-*.dll`、`ucrtbase.dll`、`libtommath.dll`
- 任何来自 Miniconda 的 DLL
- `_internal` 目录

然后用干净环境启动（`PATH` 只有 `C:\Windows\System32;C:\Windows`，去掉 `CONDA_*`、`PYTHONPATH`、`QT_PLUGIN_PATH`，工作目录不要放在仓库里）。窗口出现，并且本地页面画出来。

这条测试仍用得到本机 System32 里的系统运行库。它能抓住“包内私有 DLL 盖住系统库”，不能代替对方电脑。

### 7. 交付

做成单文件就交付带时间戳的 exe。做不成就交付带时间戳的 zip，不要把散开的目录或 `_internal` 交给用户。说明目标系统是 **64 位 Windows 10 或更新**。Windows 7 没有系统里的 Universal CRT，官方 Python 起不来。先退出旧程序再覆盖；打包时若 `PermissionError` / 拒绝访问，旧文件还在。报错行号不变，不能说明他们跑的是旧文件。

## 失败对照

| 现象 | 处理 |
|---|---|
| `找不到指定的模块` / 错误 126 | 包里仍有 conda 的 `api-ms-win`、`ucrtbase`，或 Qt 来自 conda。回到第 1 步，用官方 Python 重打 |
| `no Qt platform plugin could be initialized` | 缺 `qwindows.dll`，或 `QT_PLUGIN_PATH` 指到另一套 Qt |
| 窗口在，网页空白 / WebEngine 进程退出 | 缺 `QtWebEngineProcess.exe`、`.pak`、`icudtl.dat` 或 `d3dcompiler_47.dll` |
| 这台电脑正常，新电脑不行 | 核对的是旧目录，或过滤没进最终 COLLECT |
| 打包日志成功但文件时间没变 | 目标 exe 正被占用，产物没有替换。改用带时间戳的新文件名 |
| 单文件能启动但页面空白 | 资源路径用了 exe 所在目录。改成 `sys._MEIPASS`。WebEngine 子进程仍失败就改走 zip |
| 目录里出现 `_internal` | 单文件不要 `COLLECT`。onedir 设 `contents_directory='.'`，再把目录压成 zip |

## 附加资源

- spec、钩子和目录清单：[reference.md](reference.md)
