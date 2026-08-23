---
name: autodl-disk-cleanup
description: >-
  Diagnose and free space on AutoDL instances: system overlay (/) vs data disk
  (/root/autodl-tmp). Safely clean /tmp artifacts, apt/pip caches, and migrate
  large dirs (miniconda3, venvs, Node tarballs) to autodl-tmp with symlinks.
  Use when the user says 系统盘满了, disk full, 清理 autodl, 释放空间, overlay 100%,
  or before installing large packages on AutoDL.
---

# AutoDL 磁盘清理

AutoDL 实例通常有**两块盘**：

| 挂载点 | 典型容量 | 用途 |
| --- | --- | --- |
| `/`（overlay） | ~30 GiB | 系统盘：conda、venv、`/tmp`、apt 缓存 |
| `/root/autodl-tmp` | 数十~数百 GiB | 数据盘：数据集、checkpoint、可迁移的大目录 |

`/autodl-pub` 为共享 NFS，**不要删除或迁移**。

## 0. 先诊断（任何删除/迁移之前）

```bash
python3 scripts/check_disk.py
# 或
bash scripts/autodl_cleanup.sh --check
```

关注：

- `/` 使用率 **≥ 90%** → 优先处理系统盘
- `du -xsh /root/* /tmp` 中 **>1 GiB** 且不在 `autodl-tmp` 上的目录

常见系统盘大户（按经验）：

| 路径 | 说明 |
| --- | --- |
| `/root/miniconda3` | conda 根环境，常 15–30 GiB |
| `/root/*_env`、`*venv*` | Python 虚拟环境 |
| `/tmp/*.hdf5`、`/tmp/convert_*` | 训练/转换临时文件 |
| `/tmp/node-*`、`node.tar.xz` | 未完成的 Node 下载 |
| `/var/cache/apt` | apt 包缓存 |

## 1. 推荐清理顺序

复制并跟踪：

```
Task Progress:
- [ ] 1. check_disk.py / --check：记录清理前 df 与 Top 目录
- [ ] 2. --clean-tmp：删 /tmp 测试产物（安全）
- [ ] 3. --clean-apt：apt-get clean
- [ ] 4. --clean-pip：pip cache purge（可选）
- [ ] 5. --move-conda / --move-path：大目录迁到 autodl-tmp + 软链
- [ ] 6. 验证：df -h /、python -V、conda 仍可用
- [ ] 7. 写日志到 /root/autodl-tmp/disk_cleanup.log
```

### 一键（诊断 + 安全清理 + 迁移 conda/常见 venv）

```bash
bash scripts/autodl_cleanup.sh --apply
```

### 仅查看将执行的操作

```bash
bash scripts/autodl_cleanup.sh --dry-run
```

### 迁移指定目录到 autodl-tmp

```bash
bash scripts/autodl_cleanup.sh --move-path /root/GraspVLA_env
bash scripts/autodl_cleanup.sh --move-path /root/miniconda3
```

迁移规则：**真实目录** `mv` 到 `/root/autodl-tmp/<basename>`，原路径建**同名软链**。已有软链则跳过。

## 2. 安全边界

**可以做**

- 删除 `/tmp` 下明确的测试/基准文件（`.hdf5`、`*_test`、未解压的 `node*.tar.xz`）
- `apt-get clean`、`pip cache purge`
- 将 `/root/miniconda3`、自定义 venv 迁到 `autodl-tmp` 并软链回来
- 将 Node 官方 tarball 解压到 `/root/autodl-tmp/node-v*/`（系统 apt 的 npm 常与 Node 版本不匹配）

**不要做**

- 删除 `/usr`、`/opt`、系统 Python、CUDA 驱动相关路径
- 删除 `/root/autodl-tmp` 内用户数据集、checkpoint、`.git` 仓库（除非用户明确要求）
- 删除 `/autodl-pub` 或 `~/autodl-pub` 软链目标
- `rm -rf /root/autodl-tmp` 或整目录 `miniconda3` 无备份迁移

## 3. 迁移后验证

```bash
df -h / /root/autodl-tmp
ls -la /root/miniconda3 /root/GraspVLA_env   # 应为 -> autodl-tmp/...
/root/miniconda3/bin/python -V
which conda && conda info | head -5
```

若 `npm` 报错 `Cannot find module 'semver'`：不要用 apt 的 npm，改用数据盘 Node：

```bash
export PATH="/root/autodl-tmp/node-v22.14.0-linux-x64/bin:$PATH"
node -v && npm -v
```

（可用 `scripts/install_node.sh` 安装到数据盘。）

## 4. 输出格式

向用户汇报时包含：

1. **清理前/后** `df -h /` 与 `/root/autodl-tmp`
2. **已执行项**（删除 / 迁移 / 软链路径）
3. **释放空间**估算
4. **日志路径**：`/root/autodl-tmp/disk_cleanup.log`

## 5. 脚本说明

| 脚本 | 作用 |
| --- | --- |
| `scripts/check_disk.py` | 打印双盘使用率与 Top 大目录（`-x` 仅统计 overlay） |
| `scripts/autodl_cleanup.sh` | `--check` / `--dry-run` / `--apply` 及分项开关 |
| `scripts/install_node.sh` | 在 autodl-tmp 安装官方 Node LTS（含 npm） |

详细阈值与案例见 [reference.md](reference.md)。
