---
name: archive-split-restore
description: >-
  Split large archive/package files into fixed-size byte chunks and restore them
  later (gz, tar, tar.gz, zip, 7z, and other formats as opaque binaries). Use when
  the user mentions 分割压缩包, split archive, 分卷, restore chunks, gz_splitter,
  splitter.py, 大文件分片上传, or AutoDL size limits for zip/tar.gz.
---

# 归档 / 压缩包分片与恢复

把**已打包或已压缩的文件**按原始字节切成固定大小分片，便于上传/网盘限额；对方用同一工具合并还原。

**原则：只切文件字节流，不解压、不重新打包。**  
（`autodl-tmp/gz_splitter.py` 用 `gzip.open` 读入会先解压，切出来的块无法还原成合法 `.gz`，不要用那种写法。）

## 何时使用

- 大 `.zip` / `.tar.gz` / `.gz` / `.tar` / `.7z` 超过平台单文件限制  
- 需要把桌面发布包、数据集压缩包拆成多份传输  
- 用户提到 `splitter.py`、`gz_splitter.py`、分卷、restore chunks  

## 工作流

```
Task Progress:
- [ ] 1. 确认源文件路径与目标块大小（默认 80MB）
- [ ] 2. split → 得到 <stem>_chunks/ + *.metadata + *.partNNN.archunk
- [ ] 3. 传输整个 chunks 目录
- [ ] 4. restore → 校验大小 / SHA256，可选格式抽检
```

在 skill 目录下执行：

```bash
# 分割（推荐）
python3 scripts/archive_split_restore.py split /path/to/file.tar.gz -s 80

# 任意后缀
python3 scripts/archive_split_restore.py split /path/to/App.zip -s 50 --force

# 指定分片输出目录
python3 scripts/archive_split_restore.py split big.7z -o /tmp/big_chunks -s 100

# 恢复
python3 scripts/archive_split_restore.py restore /path/to/file_chunks -o restored.tar.gz
```

## 支持格式

| 类型 | 后缀（示例） | 说明 |
|---|---|---|
| 复合归档 | `.tar.gz` `.tgz` `.tar.bz2` `.tar.xz` | 按复合后缀剥名 |
| 压缩/归档 | `.gz` `.bz2` `.xz` `.zst` `.tar` `.zip` `.7z` `.rar` | 原样字节切分 |
| 安装包等 | `.whl` `.deb` `.rpm` `.iso` `.dmg` | 同上 |
| 其他 | 任意 | 加 `--force` |

块文件统一扩展名：`.archunk`。  
恢复时兼容旧脚本产物：`.gzchunk` / `.tarchunk`（见 [reference.md](reference.md)）。

## 产物布局

```
<stem>_chunks/
  <stem>.metadata          # original_name, total_chunks, total_size, sha256, ...
  <stem>.part000.archunk
  <stem>.part001.archunk
  ...
```

## Agent 注意

1. **大文件必须流式读写**（本脚本已实现）；禁止 `f.read()` 整文件进内存。  
2. 分割前确认磁盘空间 ≈ 原文件大小（分片总和）。  
3. 恢复后看脚本输出的大小 / SHA256；gzip/tar/zip 抽检失败时先查是否传丢块。  
4. 不要对「已是分片目录」再 split；不要对明文目录 split——应先打成 zip/tar.gz。  
5. 与桌面打包 skill 配合：可先 `scheme-a-linux-to-*-desktop` 出 zip，再用本 skill 分片。  

## 附加资源

- 与旧脚本差异、元数据字段：[reference.md](reference.md)
