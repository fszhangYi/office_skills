---
name: graspvla-repro
description: >-
  Reproduce GraspVLA local inference (PKU-EPIC Model Server + offline_test on
  port 6006). Always run a hard preflight on disk, cgroup memory, and CUDA;
  print Exit reasons and stop if the host is unfit. Follows
  GraspVLA_手把手复现教程.md (two-phase: curl download without GPU, then cu128
  torch + serve). Use when the user asks to 复现 GraspVLA, install GraspVLA,
  run serve 6006 / offline_test, or check whether this machine can install it.
---

# GraspVLA 复现

最小验收：**Model Server + `offline_test --port 6006`**（指令 → bbox + 动作）。不是 LIBERO，也不是真机。

逐步命令、坑点和版式以 [GraspVLA_手把手复现教程.md](GraspVLA_手把手复现教程.md) 为 **ref**（照抄目录变量、端口 6006、curl 下载、cu128）。

## 0. 硬门禁（任何步骤之前）

先跑预检，**失败必须停**：把脚本打印的 `Exit reasons` 原样告诉用户，不要绕过、不要继续 clone/装包/serve。

```bash
# 无 GPU / 只下载权重与骨干
python3 scripts/check_prereqs.py --phase download

# 要装 torch、起 6006、跑 offline_test
python3 scripts/check_prereqs.py --phase serve

# 从零做到验收（默认）：磁盘 + 内存 + CUDA 一起查
python3 scripts/check_prereqs.py --phase all
```

可选：`--data-root /path/GraspVLA_repro`、`--env-path /root/GraspVLA_env`（或环境变量 `GRASPVLA_ROOT` / `GRASPVLA_ENV`）。

失败时脚本以 **exit 1** 结束，并打印：

```text
GraspVLA preflight: FAIL
Exit reasons:
  1. [disk] ...
  2. [cuda] ...
```

阈值（与教程一致）：

| 项 | 不通过则退出 |
| --- | --- |
| 系统盘 `/` | 建环境/装 torch 时剩余 **&lt; 12 GiB**（已有可用 env 则可放宽） |
| 数据盘 | 从零 **&lt; 25 GiB**；权重/hub 已齐则只需余量 |
| CUDA / GPU | `serve`/`all`：无 `nvidia-smi`、显存 **&lt; 10 GiB**、驱动 CUDA **&lt; 12.0** |
| 工具 | 缺 `git` 或 `curl` |
| 环境 | `serve`/`all` 且既无 conda、也无已装 torch 的 prefix |

cgroup **&lt; 8 GiB** 不单独判失败（教程在 2 GiB 下用 curl 下完），但必须走 curl，禁止 `hf download`。

## 1. 选阶段

| 预检 phase | 做什么 | GPU |
| --- | --- | --- |
| `download` | clone + curl 主权重 12.6GB + 三块骨干 hub | 不要 |
| `serve` | conda 3.9.19 + torch 2.7.1+cu128 + 依赖 + `serve 6006` + `offline_test` | 要 |

无卡时只跑 `download`；挂卡后先 `--phase serve` 再装环境。

## 2. 按教程执行

预检通过后打开 ref，按节做，不要改端口、不要发明另一套路径：

1. 固定目录：教程 **§A.2**（`GRASPVLA_ENV` / `GRASPVLA_ROOT` / `HF_HOME`）
2. clone：§B（AutoDL 下载开 `source /etc/network_turbo`）
3. 主权重 curl：§F（2 GiB cgroup 禁止 `hf download`）
4. 骨干 hub：§G.1.1，用本 skill 的 `scripts/hf_hub_curl_download.py`（跳过重复 `pytorch_model.bin`）
5. **关 turbo** 再 conda / pip / torch：§C–§E；pytorch.org 大文件超时走 §D.3
6. serve：§G.2（`HF_ENDPOINT=https://hf-mirror.com` 做 HEAD；**不要** `HF_HUB_OFFLINE=1`）
7. 验收：§H `offline_test --port 6006`，期望 `Task: pick up pen` 且对比图左右 bbox 一致

网络分流（教程读前须知 §5）：turbo **只**给 GitHub/HF；装包必须 `unset` 代理和 `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE`。

## 3. 验收与停止

成功：日志出现 `Started server on port 6006`，`offline_test` 写出 `visualization/trial-20250507120350_visualization.png`。

停服务：`pkill -f 'vla_network.scripts.serve'`。

不要把 bbox 一致说成 LIBERO/真机成功率。
