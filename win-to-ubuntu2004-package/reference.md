# 核对 ELF 的做法

打包机是 Windows，读文件字节即可，不需要在 Linux 上跑 `readelf`。

## glibc 符号

在 ELF 内容里找 `GLIBC_(\d+)\.(\d+)`，取最大的一对。没有匹配的 ELF 不算通过。任何一个大于 `(2, 31)` 就停止打包。链接器按 SKILL 第 5 步先删再扫。

## `$ORIGIN`

`bin/python`、`bin/python3`、`bin/python3.12` 里至少有一个文件包含 ASCII `$ORIGIN`。conda-forge 的 CPython 用它指向 `$ORIGIN/../lib`。没有这段字符串就不要交付。

## DT_NEEDED

只处理 ELFCLASS64。程序头 `PT_LOAD = 1` 用来把虚拟地址换回文件偏移，`PT_DYNAMIC = 2` 是动态段。动态项里 `DT_NEEDED = 1` 的值是字符串表偏移，`DT_STRTAB = 5` 是字符串表虚拟地址。

对每个需要的 soname：

- 包内任意文件的文件名与它相同，算包内已带。
- 否则只允许这些系统基线：`libc.so.6`、`libm.so.6`、`libdl.so.2`、`libpthread.so.0`、`librt.so.1`、`libutil.so.1`、`libresolv.so.2`、`libcrypt.so.1`、`ld-linux-x86-64.so.2`、`linux-vdso.so.1`。

多出来的名字就是目标机上可能没有的库，停止打包。同名文件存在不表示符号版本够用，所以这一步不能代替 glibc 扫描。

## 已知通过的一次结果

按本流程打出的目录里有 457 个 ELF，DT_NEEDED 没有落在包外（除了上面的 glibc 基线）。该 tar.gz 在 Ubuntu 20.04 上一次启动成功。这不能代替下一次打包仍要重跑五道门。
