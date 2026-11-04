---
name: win-to-ubuntu2004-package
description: >-
  On Windows, build a self-contained x86_64 tar.gz that runs on Ubuntu 20.04
  (glibc 2.31, X11) without PyInstaller cross-compile, WSL, or Docker. Uses
  micromamba only to solve a linux-64 conda-forge prefix, then extracts
  packages in Python because Windows cannot create the symlinks. Use when the
  user asks to package on Windows for Ubuntu 20.04, glibc 2.31, linux-64
  prefix, micromamba cross install, or win-to-ubuntu2004-package. Not
  Windows-to-Windows and not Linux-to-Linux PyInstaller.
---

# Windows 上打出 Ubuntu 20.04 能运行的包

在 **Windows 构建机** 上做出一个目录，打成 `tar.gz`。Ubuntu 20.04 x86_64 解压后用包里的 Python 启动。目标机不装 Python、不装 conda。

PyInstaller 不能跨系统编译。没有 WSL、也没有 Docker 时，用这条路径。不要用 `scheme-a-linux-to-linux-desktop`（那是在 Linux 上跑 PyInstaller）。

Ubuntu 20.04 的 glibc 是 **2.31**，系统 Python 是 **3.8**。Pillow 13 需要 Python ≥ 3.10，所以必须自带解释器。图形程序按 **X11** 来打；Wayland 上的键鼠注入不可靠。

## 工作流

```
Task Progress:
- [ ] 1. micromamba 只做 --dry-run，解出 linux-64 的包清单
- [ ] 2. 从镜像下载，校验 sha256
- [ ] 3. 用 Python 展开；符号链接改成文件副本
- [ ] 4. noarch python 的 site-packages 挪进 lib/python3.12/
- [ ] 5. 展开完再删掉需要 glibc 2.36 的链接器
- [ ] 6. 纯 Python 轮子（例如截屏库 mss）从 PyPI 装进 site-packages
- [ ] 7. 放入应用，写 LF 启动脚本
- [ ] 8. 过 glibc、Tk、$ORIGIN、导入路径、DT_NEEDED 五道门
- [ ] 9. 打带时间戳的 tar.gz
```

打包脚本用 **Python 3.14**（标准库有 `compression.zstd`）。micromamba 用 win-64 的 2.x，已知 2.3.3 可用。

### 1. 只求解，不安装

```
micromamba create --dry-run --json -y -p <prefix> --platform linux-64 --override-channels -c conda-forge <specs>
```

环境变量：

- `MAMBA_ROOT_PREFIX` 指向构建目录
- `CONDA_PLUGINS_AUTO_ACCEPT_TOS=yes`
- `CONDA_OVERRIDE_LINUX=5.4.0`
- `CONDA_OVERRIDE_GLIBC=2.31`

必须 `--override-channels`。不设的话 micromamba 会去拉 `repo.anaconda.com` 的 defaults，在这台网络上会超时。conda-forge 的 repodata 失败时，换 `https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge` 再解一次。

桌面程序的一组能解出来的规格：`python=3.12` `pillow=13` `pynput` `tk` `python-xlib` `xorg-libx11`。不要把 conda 包名 `mss` 写进去，见下面的坑。

读 JSON 的 `actions.LINK`。每项要有 `url`、`sha256`、`fn`、`depends`。`__glibc >=x.y` 里的下限若高于 2.31，停止。

### 2. 下载

把 `https://conda.anaconda.org/conda-forge/` 换成清华镜像再下。镜像失败再试原地址。sha256 不对就丢掉。缓存放在 `build/conda-pkgs`，下次按哈希跳过。

### 3. 在 Windows 上展开

这台系统执行 `mklink` 会得到 **You do not have sufficient privilege**。`micromamba create` 会在解包时创建 `libfoo.so -> libfoo.so.1`，然后报 `Can't create`。不要提权去解包，改成自己展开：

- `.conda` 是 zip：`pkg-*.tar.zst` 才是文件，`info-*.tar.zst` 只用来读元数据。
- 普通文件直接写出。符号链接和硬链接在目标文件落地后 **复制内容**。目录符号链接用整树复制（ncurses 的 `lib/terminfo` → `../share/terminfo`）。
- 路径逃出 prefix 就停止。多轮解析链接链。

副本比符号链接大，运行时等价。不要把 conda 的 255 字节前缀占位符改写成 Windows 路径。CPython 靠可执行文件旁边的 `lib/python3.12/os.py` 和二进制里的 `$ORIGIN` 找家。

### 4. noarch python

`info/link.json` 里 `noarch.type == python` 时，包内路径是 `site-packages/...`，必须改写成 `lib/python3.12/site-packages/...`。二进制包通常没有 `link.json`，这不是错误。

漏掉这一步时，`Xlib` 和 `six` 会落在 prefix 根上的 `site-packages/`。pynput 在 Linux 上 `import Xlib` 失败，键鼠注入起不来。Pillow、pynput 这类 linux-64 包本身就带 `lib/python3.12/`，不要对它们再加一层。

### 5. 链接器

`ld_impl_linux-64` 里的 `ld` 实际需要 **GLIBC_2.36**，元数据却写着 `>=2.17`。它只在编译时用。先让 python 包里的 `compiler_compat/ld` 链接能展开，再删掉文件名是 `ld` 或以 `-ld` 结尾、且 glibc 高于 2.31 的 ELF。不要在展开前丢掉整个包，否则那条链接没有目标。

### 6. PyPI 上的纯 Python 包

conda-forge 上的 `mss` 是另一套大型科学软件，会拉下数百 MB。截屏库是 PyPI 的 `mss`（纯 Python wheel）。`pip download --only-binary=:all: --no-deps`，轮子里若有 `.so` / `.pyd` 就拒绝。解压到 `lib/python3.12/site-packages`。官方 PyPI 失败再用 `https://pypi.tuna.tsinghua.edu.cn/simple`。

### 7. 应用和启动脚本

应用放在 `prefix/app`。启动脚本用 LF，不要用 Windows 换行：

```sh
#!/bin/sh
cd "$(dirname "$0")" || exit 1
ROOT=$(pwd)
export PYTHONNOUSERSITE=1
export PYTHONPATH="$ROOT/app${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$ROOT/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$ROOT/lib/tcl8.6"
export TK_LIBRARY="$ROOT/lib/tk8.6"
exec "$ROOT/bin/python" -m <模块> <子命令>
```

Tk 的 conda 包常常是 `noxft`。X11 上能开窗口。`TCL_LIBRARY` / `TK_LIBRARY` 指到包内的 `tcl8.6` 和 `tk8.6`。

### 8. 打 tar 之前的门

不过就停止，不要把半成品交出去。

| 门 | 要求 |
|---|---|
| glibc | 每个 ELF 里最高的 `GLIBC_x.y` ≤ 2.31 |
| 可搬动 | `bin/python*` 含 `$ORIGIN` |
| Tk | 存在 `lib/python*/lib-dynload/_tkinter*.so` |
| 导入 | `Xlib`、`six`、`PIL`、`pynput`、项目用到的纯 Python 库在 `lib/python3.12/site-packages` |
| 动态库 | 每个 ELF 的 `DT_NEEDED` 要么是包内同名文件，要么是系统 glibc 基线：`libc.so.6` `libm.so.6` `libdl.so.2` `libpthread.so.0` `librt.so.1` `libutil.so.1` `libresolv.so.2` `libcrypt.so.1` `ld-linux-x86-64.so.2` |

扫描方法见 [reference.md](reference.md)。

### 9. 归档

`tar.gz`，目录名和文件名带 `ubuntu2004-x86_64` 和本地时间 `YYYYMMDD-HHMMSS`。`.sh`、`bin/` 下的文件、文件名含 `.so` 的设为 `0755`。不要覆盖一个正在使用的固定文件名。

Windows 上不能执行这些 ELF。静态门通过只能说明不像会因为 glibc 或少库立刻起不来。交给用户时写明：要在 Ubuntu 20.04 的 **X11** 桌面里执行启动脚本，才算跑过。

## 坑

| 现象 | 原因 |
|---|---|
| `repo.anaconda.com` 超时 | 没加 `--override-channels`，solver 还在找 defaults |
| `glibc version not found` | 没设 `CONDA_OVERRIDE_GLIBC` / `CONDA_OVERRIDE_LINUX` |
| 一次装下几百个包、含 Qt WebEngine | conda 的 `mss` 不是截屏库 |
| `Can't create` `libfoo.so` | Windows 不能建符号链接；不要用 `micromamba create` 解包 |
| `无法展开链接：lib/terminfo` | 那是目录符号链接，要复制整棵树 |
| `import Xlib` 失败 | noarch python 仍放在 prefix 根的 `site-packages/` |
| `info/link.json` 不存在 | 二进制包本来就没有；只在 noarch 判断时跳过 |
| 链接器 glibc 2.36 | 元数据偏低；展开后删掉 `ld` |
| 官方 conda 下载被重置 | 改下清华镜像，仍用求解结果里的 sha256 |
