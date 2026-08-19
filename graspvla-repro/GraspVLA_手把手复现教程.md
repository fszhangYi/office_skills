# GraspVLA 手把手复现教程（本机实测细化版）

> 仓库：[PKU-EPIC/GraspVLA](https://github.com/PKU-EPIC/GraspVLA)（CoRL 2025）  
> 论文：[arXiv:2505.03233](https://arxiv.org/abs/2505.03233)｜项目页：[GraspVLA-web](https://pku-epic.github.io/GraspVLA-web/)  
> 实测机：AutoDL；数据盘 `/root/autodl-tmp`（约 150G）+ 系统盘 `/`（约 30G）；GPU 阶段为 **RTX 5090 D 32GB**  
> **本教程验收端口：`6006`**（官方示例常用 6666，二者等价，以本教程为准）  
> **进度（2026-08-19）：** 无 GPU 阶段（clone + 主权重 + 三块骨干）与 GPU 阶段（conda + cu128 torch + serve 6006 + `offline_test`）均已完成并通过验收。

---

## 这项工作是什么：为何值得复现

读操作步骤之前，先用一页纸钉住 **GraspVLA 要解决的问题、突破点、贡献**。后面花两小时下权重、起服务，验收的不是“能跑一个脚本”，而是在验证：**纯合成动作数据预训练出来的抓取 VLA，能否在本机完成加载与开集指令推理**。

### 问题：VLA 被真实机器人数据卡住

近年视觉–语言–动作（Vision-Language-Action, VLA）模型（如 RT-2、OpenVLA 及带 action expert 的后继工作）把互联网视觉语言模型接到机械臂上，零样本与少样本适应成为卖点。瓶颈很具体：**真实机器人示教贵、慢、难覆盖物体与场景分布**。多数现成 VLA 仍要靠域内后训练才能部署。合成数据成本更低，但 sim-to-real 与语义覆盖不足，长期被当成“凑数”，而不是可独立支撑的预训练主数据。

GraspVLA（北京大学等，[CoRL 2025](https://arxiv.org/abs/2505.03233)）问的是： **能不能几乎只用大规模合成动作数据，把抓取 VLA 预训练到可以直接上真机、且开词汇泛化的程度？**

### 突破点（读者只需记住三条）

1. **数据突破：SynGrasp-1B。** 在仿真中用真实感渲染与域随机化生成约 **十亿帧** 抓取数据，覆盖约 **240 类、一万余物体**。把“合成数据规模不够、外观不够乱”这条常见反对意见，用体量与随机化正面顶住。
2. **训练突破：只用合成动作做预训练，仍追求直接 sim-to-real。** 官方主张 GraspVLA 在真实抓取上可 **零样本、不微调** 迁移；这与“合成数据只能当预热、真机必须再采一遍”的惯常流程相对。
3. **结构突破：统一 Chain-of-Thought（文中称 Progressive Action Generation, PAG）。** 同一条推理链里先做 **自回归感知**（如 2D 框），再对合成数据补上 **抓取位姿 + flow matching 动作块**。互联网语义数据只训练 CoT 的感知前段，合成数据训练整条链。这样语义开集（网上见过的物体名）和几何交互（仿真里学过的抓）可以拼在一个模型里，而不是两个系统硬接。

本机 `offline_test` 画出来的 bbox，对应的就是这条 CoT 的感知中间量；返回的 `action` 对应 flow matching 动作专家。能复现 server，等于把这条 PAG 链路在本地跑通。

### 论文贡献（与官方 README 对齐）

| 贡献 | 含义 | 本教程能验证到哪 |
| --- | --- | --- |
| SynGrasp-1B | 十亿帧合成抓取数据集 | 本教程 **不下载该数据集**（体积远超推理权重） |
| GraspVLA 预训练权重 | 在 SynGrasp-1B 上训好的抓取基础模型 | **下载 `model.safetensors` 并加载** |
| 统一 CoT / PAG | 感知与动作在同一推理过程 | **offline_test：指令 → bbox + 动作** |
| 开词汇抓取 | 合成几何 + 互联网语义联合 | 可改 `text`（如 `pick up football`）；画面须匹配才有物理意义 |
| 仿真 playground / 真机接口 | LIBERO 与真实控制 | 见文末扩展，**不在本教程最小验收内** |

### 复现的意义（避免读成“再下一个大模型”）

- **方法意义：** 验证“合成数据能否当 VLA 主预训练语料”这一主张，在工程上首先体现为：**权重能加载、CoT 中间量能出、动作能出**。没有这一步，谈零样本真机或 LIBERO 数字都还没有落地点。
- **成本意义：** 官方强调合成数据相对真机采集更便宜。复现推理侧，是用 **约 20GB 磁盘 + 约 10GB 显存 + 数小时下载**，换到可调用的抓取 VLA，而不必重训十亿帧。
- **边界（必须写清）：** 本教程证明的是 **预训练权重的本地推理复现**，不是 LIBERO 成功率复现，也不是真机抓取成功率复现。后者依赖 playground / 相机与臂。把 `offline_test` 的样例图改成 `pick up football` 只能证明指令接口是开集的，不能证明图中有足球。

公开入口：[论文 PDF](https://arxiv.org/pdf/2505.03233)、[项目页](https://pku-epic.github.io/GraspVLA-web/)、[代码](https://github.com/PKU-EPIC/GraspVLA)、[权重](https://huggingface.co/shengliangd/GraspVLA)。

---

## 读前须知

1. **本教程复现的是「Model Server + offline_test」**，不需要机械臂，也不需要装 LIBERO 仿真。这一步能证明：权重、依赖、推理链路都通了。
2. **用时标注说明**：`⏱ 本机实测` 来自本次复现日志；`⏱ 预估区间` 会随网速/磁盘变化。下载往往占总时间 70% 以上。
3. **分盘是硬要求**：主权重约 12.6GB，骨干 hub 缓存约 6–7GB。把所有东西塞进一块小盘，很容易在中途失败。
4. **GPU 不是全程都要占用。** 墙钟时间大半花在 **下载**。这些步骤 **可以无 GPU、甚至在内存很紧的 CPU 机上先做完**，再挂 GPU 加载。本机已验证：无 GPU 阶段把代码/权重/骨干都落盘了；GPU 阶段真正卡住的是 **装 cu128 torch 的网络与缓存用法**，不是「先无卡后有卡」这条策略本身。
5. **AutoDL 网络必须分流（两阶段最重要的一条）：** `source /etc/network_turbo` **只适合 GitHub / Hugging Face 大文件**。它对 pip、conda、清华源、`download.pytorch.org` **往往更慢甚至超时**。正确开关：

   | 你在做什么 | turbo / 代理 | 备注 |
   | --- | --- | --- |
   | `git clone`、curl 下 HF 权重/骨干 | **开** `source /etc/network_turbo` | 直连 `huggingface.co`；不要同时设 `HF_ENDPOINT` |
   | conda / pip / 装 torch | **关** `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY`，并 `unset REQUESTS_CA_BUNDLE SSL_CERT_FILE` | turbo 脚本还会改 CA 证书，只 unset 代理不够 |
   | 骨干已在本地、启动 serve | **关 turbo**；需要 HEAD 时再 `export HF_ENDPOINT=https://hf-mirror.com` | 见坑点 G：纯 `HF_HUB_OFFLINE=1` 会卡在缺失的 `pytorch_model.bin` |

6. **内存也可能很紧：** 本机 agent/任务 cgroup `memory.max=2GiB`（不是主机 `free -h` 显示的几百 GiB）。在此限制下，`hf download`（huggingface_hub 多 worker）会被 **OOM kill（exit 137）**。无 GPU 阶段请用 **curl 流式下载**（几乎不占内存），见 §F / §G.1.1。

### 何时可以无 GPU（墙钟时间的大头在这里）

经验法则：**凡是只往磁盘写文件、不 `torch` 上模型的步骤，都可以无 GPU；在 2GiB cgroup 下也不要跑会导入 torch 的 Python。** 真正绑 GPU 的只有「装 CUDA 版 PyTorch 之后的加载 / warmup / 推理」。

| 阶段 | 要不要 GPU | 本机是否已做 | 说明 |
| --- | --- | --- | --- |
| A. 检查磁盘 / cgroup | **否** | ✅ | 无 GPU 机只查 `df` + `memory.max` |
| B. clone 代码 | **否** | ✅ | 纯 git；turbo 下 ~7 s |
| C. 建 conda（Python 3.9） | **否** | ✅ GPU 阶段 | 无 GPU 时系统盘仅 ~5.5G，先跳过；挂卡后清 pip 缓存再建 |
| D. 装 `torch==2.7.1+cu128` | 下载否；验收要 GPU | ✅ GPU 阶段 | 无 GPU / 紧内存机 **不要装 torch**；本机 pip 直装超时，改 curl 本地 wheel 才成功 |
| E. 装 GraspVLA 依赖 | **否** | ✅ GPU 阶段 | 钉死 numpy / opencv；先关 turbo |
| F. 主权重 12.6GB | **否** | ✅ | curl 流式；本机 **~42 min** |
| G.1.1 预下载 DINO / SigLIP / InternLM | **否** | ✅ | 写入 `HF_HOME/hub`；本机 **~23 min** |
| G. 缓存已齐后启动 serve | **要** | ✅ GPU 阶段 | 加载 ~10GB 显存 + warmup；本机 warmup 后约 **2.0 it/s** |
| H. `offline_test` | **要**（server） | ✅ GPU 阶段 | `pick up pen` 左右 bbox 与官方参考一致 |

**推荐排期（租 GPU 按小时计费时）：**

1. **无 GPU 或 GPU 关机：** `source /etc/network_turbo` → clone → curl 下主权重 → curl 预下载三块骨干。
2. **再开 GPU：** 清系统盘 pip 缓存（若 `/` 紧张）→ **关 turbo** → 建 conda → 装 CUDA PyTorch 与依赖 → `serve --port 6006` → `offline_test`。

### 总时间预算（本机实测）

| 阶段 | ⏱ 本机实测（2026-08-19） | 要不要 GPU | 是否可跳过 |
| --- | --- | --- | --- |
| A. 检查磁盘 / cgroup | ~1 min | 否 | 否 |
| B. clone 代码 | **~7 s**（turbo） | **否** | 已有仓库可跳过 |
| C. 建 conda 环境 | **~20 s**（GPU 阶段；先清 `/root/.cache/pip`） | **否** | 已有环境可跳过 |
| D. 装 PyTorch cu128 | 顺利 pip 约 20–25 min；**本机 pip 直装超时**，curl 主包后本地安装约 10–15 min（不含失败重试） | 下载否；验收要 | 已装可跳过 |
| E. 装 GraspVLA 依赖 | **~3–8 min** | **否** | 已装可跳过 |
| F. 下载主权重 12.6GB | **~42 min**（turbo + curl，均速约 5 MB/s） | **否** | ✅ |
| G.1.1 预下载三块骨干 | **~23 min**（turbo + curl→hub） | **否** | ✅ |
| G. 启动 serve（缓存已齐） | **~2–5 min**（加载 + warmup） | **要** | — |
| H. offline_test 验收 | **~5–10 s**；样例推理约 **0.5 s/次** | **要** | 否（验收用） |
| **无 GPU 阶段小计** | **约 65–70 min** | 全否 | — |
| **GPU 阶段小计（顺利）** | **约 30–40 min** | 要 | 本机因 pytorch.org 超时，安装链实际更长 |

### 本机最终落盘（2026-08-19，已验收）

| 路径 | 大小 | 状态 |
| --- | --- | --- |
| `/root/autodl-tmp/report/repos/GraspVLA` | ~10 MB | ✅ 代码 |
| `/root/GraspVLA_env`（软链 `$GRASPVLA_ROOT/env`） | **~7.0 GB** | ✅ Python 3.9.19 + torch 2.7.1+cu128 |
| `.../weights/checkpoint/model.safetensors` | **12624643076 bytes（12.62 GB）** | ✅ |
| `.../hf_home/hub/models--timm--vit_large_patch14_reg4_dinov2.lvd142m` | ~1.2 GB（仅 safetensors） | ✅ |
| `.../hf_home/hub/models--timm--vit_so400m_patch14_siglip_224.v2_webli` | ~1.6 GB（仅 safetensors） | ✅ |
| `.../hf_home/hub/models--internlm--internlm2-1_8b` | ~3.6 GB | ✅ |
| `.../visualization/trial-20250507120350_visualization.png` | ~161 KB | ✅ `offline_test` 对比图 |

GPU 阶段实测：RTX 5090 D，显存约 10 GB / 32 GB；warmup 后约 **2.0 it/s**；`offline_test` 任务 `pick up pen`，左右 bbox 对齐红笔。

---

## A. 环境与磁盘检查

⏱ **本机实测：~1 min**  
**GPU：不需要。** 无 GPU 机器只跑 `df -h` 与 cgroup 内存；`nvidia-smi` 可放到 GPU 机上再做。

### A.1 看两块盘与内存上限

```bash
df -h / /root/autodl-tmp
free -h | head -2
# AutoDL / 沙箱常见：cgroup 内存远小于 free -h
cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null
# 有 GPU 时再查：
# nvidia-smi --query-gpu=name,memory.total --format=csv
```

**本机实测：** 全程 `memory.max=2147483648`（**2GiB**）；`free -h` 虽显示数百 GiB，**不能当真**。无 GPU 阶段系统盘 `/` 仅剩 **~5.5G**（miniconda ~20G + pip 缓存 ~6G），不够装 torch。GPU 阶段先 `rm -rf /root/.cache/pip/http-v2` 再建模，conda 环境最终 **~7.0G** 在 `/root/GraspVLA_env`。

**建议剩余空间（从零开始）：**

| 盘 | 建议剩余 | 原因 |
| --- | --- | --- |
| 系统盘 `/` | ≥ **12 GB** | conda + torch 解压峰值；不够时先 `rm -rf /root/.cache/pip/http-v2` **和** `/tmp/pip-unpack-*` |
| 数据盘 `/root/autodl-tmp` | ≥ **25 GB**（另加 ~3–5G 给 pip TMPDIR 更稳） | 权重 12.6G + HF 骨干 ~6–7G；系统盘紧时 TMPDIR 也改走这里 |

### A.2 本教程固定目录（请照抄，后续命令都依赖它）

```bash
# 系统盘：Python 环境（GPU 阶段再建；系统盘紧时也可改放到数据盘）
export GRASPVLA_ENV=/root/GraspVLA_env

# 数据盘：权重、HF 缓存、日志
export GRASPVLA_ROOT=/root/autodl-tmp/GraspVLA_repro
export GRASPVLA_CODE=/root/autodl-tmp/report/repos/GraspVLA
export HF_HOME=$GRASPVLA_ROOT/hf_home
# 有 network_turbo 时不要设 HF_ENDPOINT；无 turbo 再考虑：
# export HF_ENDPOINT=https://hf-mirror.com

mkdir -p "$GRASPVLA_ROOT"/{weights,hf_home,logs,visualization,tmp,scripts}
mkdir -p /tmp/pip_cache_graspvla
```

目录最终长这样：

```text
/root/GraspVLA_env                          # conda 环境（系统盘约 7.0GB）
/root/autodl-tmp/GraspVLA_repro/
  ├── env -> /root/GraspVLA_env             # 软链，conda activate 用这个
  ├── scripts/hf_hub_curl_download.py       # 紧内存下写 hub 缓存用
  ├── weights/checkpoint/model.safetensors  # 主权重 ~12.6GB
  ├── hf_home/hub/models--*                 # DINO/SigLIP/InternLM ~6–7GB
  ├── tmp/wheels/                           # GPU 阶段：curl 下来的 torch/triton .whl
  ├── logs/
  └── visualization/
/root/autodl-tmp/report/repos/GraspVLA      # 代码
```

### ⚠ 坑点 A

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| 只看总容量不看挂载点 | `df -h` 显示 100G 够，但 pip 实际写到 `/` 撑爆 | 永远分清 `/` 与 `/root/autodl-tmp`；大文件放数据盘 |
| AutoDL 系统盘只有 ~30G | 装 torch 时 `/tmp` 与 pip cache 同时膨胀 → `No space left` | 先清 `/root/.cache/pip/http-v2`；权重放数据盘；`/` 仍紧则 `TMPDIR` 改数据盘（见坑点 D） |
| `/tmp/pip-unpack-*` 残留 | 失败/中断后系统盘突然少 **~10G** | `rm -rf /tmp/pip-unpack-* /tmp/pip-install-*`；本机 GPU 阶段就是被半截 unpack 占满 |
| 只看 `free -h` | 以为有几百 GiB 内存，一跑 `hf download` 就 137 | 查 `memory.max`；紧内存用 curl，不用 hf CLI |
| 与权重下载并行装 torch | 两块盘同时涨，数据盘先满 | **串行**：先下完权重，再装 torch |

---

## B. 获取代码

⏱ **本机实测：~7 s**（`source /etc/network_turbo` 后 `git clone --depth 1`）  
**GPU：不需要。内存：几乎不占。**

```bash
source /etc/network_turbo   # AutoDL：加速 GitHub
mkdir -p /root/autodl-tmp/report/repos
cd /root/autodl-tmp/report/repos
git clone --depth 1 https://github.com/PKU-EPIC/GraspVLA.git
export GRASPVLA_CODE=/root/autodl-tmp/report/repos/GraspVLA
```

验收：

```bash
ls "$GRASPVLA_CODE/README.md" "$GRASPVLA_CODE/requirements.txt"
ls "$GRASPVLA_CODE/visualization/trial-20250507120350_data.npy"
```

---

## C. 创建 conda 环境（系统盘）

⏱ **本机实测：~20 s**（GPU 阶段；无 GPU 时因系统盘仅剩 ~5.5G 跳过，挂卡后先清 pip 缓存）  
**GPU：不需要。** 这一步只装 CPython，与 CUDA 无关。

> **无 GPU / 紧磁盘阶段可跳过本节与 §D/§E**，只做 §B + §F + §G.1.1。

### C.1 坑：清华 `pkgs/free` 频道 404

若直接 `conda create -n GraspVLA ...` 报：

```text
UnavailableInvalidChannel: HTTP 404 NOT FOUND for channel .../pkgs/free
```

**原因**：`~/.condarc` 里写了已失效的 `anaconda/pkgs/free`。  
**解决**：用 `--override-channels`，不要改全局 git/conda 配置也行：

```bash
conda create -p "$GRASPVLA_ENV" python=3.9.19 -y \
  --override-channels \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -c defaults
```

### C.2 做软链并激活

```bash
ln -sfn "$GRASPVLA_ENV" "$GRASPVLA_ROOT/env"

source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"
python -V   # 期望：Python 3.9.19
which python
```

### ⚠ 坑点 C

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| 系统盘 <12G 就 `conda create` | 后面装 torch 解压失败 | 先 `rm -rf /root/.cache/pip/http-v2`；本机清完才建模成功 |
| 环境建在数据盘 | 数据盘本就紧张，torch 再占 6–8G | 优先 `/root/GraspVLA_env`，再用 `ln -sfn` 指到 `$GRASPVLA_ROOT/env` |
| `conda activate` 无效 | `CommandNotFoundError` | 先 `source .../conda.sh` |
| Python 版本不对 | 官方示例 3.9.19；3.12 可能装不上指定 torch wheel | 严格用 3.9.19 |

---

## D. 安装 PyTorch（最容易炸磁盘、也最容易「假死」的一步）

⏱ **顺利 pip：~20–25 min**；**本机实测：pip 直装失败（pytorch.org 大文件超时），改 curl 本地 wheel 后安装约 10–15 min**  
**GPU：下载与 `pip install` 不需要 GPU**。`python -c "import torch; print(torch.cuda.is_available())"` 以及之后的 serve **需要 GPU**。

> **先关 turbo。** 装包前必须：
> ```bash
> unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
> unset REQUESTS_CA_BUNDLE SSL_CERT_FILE   # turbo 脚本也会设这两项
> unset OMP_NUM_THREADS
> ```
> 本机 RTX 5090 D 用 `cu128` **完全可用**；装不上不是卡与 CUDA 不兼容。

### D.1 安装命令（网络顺时照抄）

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"

# `/` 剩余 ≥12G 时临时文件走系统盘；更紧则改成 $GRASPVLA_ROOT/tmp/pip_tmp
export TMPDIR=/tmp
export PIP_CACHE_DIR=/tmp/pip_cache_graspvla
mkdir -p "$PIP_CACHE_DIR"

pip install torch==2.7.1 torchvision==0.22.1 \
  --index-url https://download.pytorch.org/whl/cu128
```

nvidia 小包（几百 MB）通常能下完；若日志出现下面这样，**不要干等**，直接跳 §D.3：

```text
Downloading ... torch-2.7.1+cu128 ... (1039.4 MB)
WARNING: Connection timed out while downloading.
... resume 9.4 MB ...
WARNING: Connection timed out ...
```

### D.2 验证

```bash
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
print("gpu", torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
x = torch.zeros(1, device="cuda")
print("cuda_tensor_ok", x.device)
PY
```

期望类似：

```text
torch 2.7.1+cu128
cuda True
gpu NVIDIA GeForce RTX 5090 D
cuda_tensor_ok cuda:0
```

### D.3 本机最终成功路径：curl 三大 wheel + `--no-deps`（pytorch.org 超时时用）

pip 对 **~1GB 的 torch 主包** 续传很脆；同一 URL 用 `curl -C -` 写到数据盘，本机约 **7 MB/s** 能下完。然后 **禁止再让 pip 去 pytorch.org 拉 torch/triton**。

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
unset REQUESTS_CA_BUNDLE SSL_CERT_FILE

export GRASPVLA_ROOT=/root/autodl-tmp/GraspVLA_repro
W="$GRASPVLA_ROOT/tmp/wheels"
mkdir -p "$W" "$GRASPVLA_ROOT/tmp/pip_tmp" "$GRASPVLA_ROOT/tmp/pip_cache"
cd "$W"

# 1) 主包落到数据盘（可断点续传）
curl -L --fail --retry 40 --retry-delay 8 --connect-timeout 30 -C - \
  -o torch-2.7.1+cu128-cp39-cp39-manylinux_2_28_x86_64.whl \
  "https://download.pytorch.org/whl/cu128/torch-2.7.1%2Bcu128-cp39-cp39-manylinux_2_28_x86_64.whl"
curl -L --fail --retry 40 --retry-delay 8 --connect-timeout 30 -C - \
  -o torchvision-0.22.1+cu128-cp39-cp39-manylinux_2_28_x86_64.whl \
  "https://download.pytorch.org/whl/cu128/torchvision-0.22.1%2Bcu128-cp39-cp39-manylinux_2_28_x86_64.whl"
curl -L --fail --retry 40 --retry-delay 8 --connect-timeout 30 -C - \
  -o triton-3.3.1-cp39-cp39-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl \
  "https://download.pytorch.org/whl/triton-3.3.1-cp39-cp39-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"

source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"
export TMPDIR="$GRASPVLA_ROOT/tmp/pip_tmp"          # 系统盘紧时务必改数据盘
export PIP_CACHE_DIR="$GRASPVLA_ROOT/tmp/pip_cache"

# 2) 只装三个本地 wheel，不要解析网上依赖（否则 pip 又会去下 triton）
pip install --no-deps \
  "$W"/torch-2.7.1+cu128-cp39-cp39-manylinux_2_28_x86_64.whl \
  "$W"/torchvision-0.22.1+cu128-cp39-cp39-manylinux_2_28_x86_64.whl \
  "$W"/triton-3.3.1-cp39-cp39-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl

# 3) CUDA 运行库：优先吃已有 pip cache；缺的再走 nvidia 源（不要走 pytorch.org）
pip install \
  nvidia-cuda-nvrtc-cu12==12.8.61 nvidia-cuda-runtime-cu12==12.8.57 \
  nvidia-cuda-cupti-cu12==12.8.57 nvidia-cudnn-cu12==9.7.1.26 \
  nvidia-cublas-cu12==12.8.3.14 nvidia-cufft-cu12==11.3.3.41 \
  nvidia-curand-cu12==10.3.9.55 nvidia-cusolver-cu12==11.7.2.55 \
  nvidia-cusparse-cu12==12.5.7.53 nvidia-cusparselt-cu12==0.6.3 \
  nvidia-nccl-cu12==2.26.2 nvidia-nvtx-cu12==12.8.55 \
  nvidia-nvjitlink-cu12==12.8.61 nvidia-cufile-cu12==1.13.0.11 \
  --extra-index-url https://pypi.nvidia.com

# 4) Python 小依赖：清华源或 curl 到 $W/deps 后再 --no-index（见坑点 D）
pip install filelock 'typing-extensions>=4.10.0' 'sympy>=1.13.3' \
  networkx jinja2 fsspec 'numpy<2.1' 'pillow!=8.3.*,>=5.3.0' \
  'mpmath<1.4,>=1.1.0' MarkupSafe \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

然后做 §D.2 验证。§E 会把 numpy 钉回 **1.26.4**（torch 可能先拉来 2.0.x，没关系）。

### ⚠ 坑点 D

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| **pytorch.org 大文件超时** | `Connection timed out while downloading` torch ~1GB；反复 resume 几 MB | **不是 cu128 装不上**。停 pip，改 §D.3 `curl -C -` |
| **`--find-links=$PIP_CACHE_DIR` 扫不到包** | `No matching distribution found for filelock` | `PIP_CACHE_DIR` 是 **http-v2 哈希目录**，不是平铺 `.whl`。`--find-links` 无效。把缓存里的 `*.whl` `find` 复制到平铺目录，或直接 `--no-deps` |
| 只传了 torch/torchvision 本地 wheel | pip 仍去 `download-r2.pytorch.org` 拉 **triton 155MB**，再次超时 | 三个 wheel **都**用本地路径；或 `--no-deps` |
| `network_turbo` 还开着 | pip/conda/pytorch 极慢或超时 | 装包前 unset 代理 **和** `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE` |
| `TMPDIR=/tmp` 且 `/` 很紧 | 半截 `pip-unpack-*` 占满系统盘（本机约 10G） | `rm -rf /tmp/pip-unpack-*`；改 `TMPDIR=$GRASPVLA_ROOT/tmp/pip_tmp` |
| `files.pythonhosted.org` 超时 | pillow 等小包卡住 | 换清华源；仍慢则 curl 到本地再 `pip install --no-index --find-links` |
| 清华源 pip 只有几十 KB/s | numpy 下半小时不动 | 同一 URL 用 curl（本机 curl 明显快于 pip） |
| 根分区 pip 旧缓存占 7GB+ | `/` 只剩几 GB，装到一半失败 | `rm -rf /root/.cache/pip/http-v2` |
| 命令被 `\| tail` 包住看起来“卡住” | 其实在下 1GB 的 torch wheel | 另开终端看 wheel 体积是否增长 |
| 误判「5090 不能用 cu128」 | 装很久没成功 | 本机 **5090 D + torch 2.7.1+cu128** 已跑通 serve |
| 与 `hf download` 并行 | 磁盘/带宽互相抢 | **不要并行** |

---

## E. 安装 GraspVLA Python 依赖

⏱ **本机实测：~3–8 min**（opencv wheel 较大，约 70MB+）  
**GPU：不需要。** `transformers` / `opencv` 等均为 CPU 安装。

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"
cd "$GRASPVLA_CODE"

# `/` 紧时改数据盘，与 §D 相同
export TMPDIR=/tmp
export PIP_CACHE_DIR=/tmp/pip_cache_graspvla
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
unset REQUESTS_CA_BUNDLE SSL_CERT_FILE

# 注意：不要直接 pip install -r requirements.txt 再让 pip 重装 torch
# 下面显式跳过已装好的 torch，并钉死 numpy / opencv 版本
pip install transformers==4.53.1 numpy==1.26.4 \
  'Pillow>=8.0.0' 'pydantic>=2.0.0' 'timm>=0.9.0' \
  'tqdm>=4.60.0' 'pyzmq>=25.0.0' 'transforms3d>=0.4.0' \
  'safetensors>=0.3.0' 'typing-extensions>=4.0.0' \
  opencv-python==4.10.0.84 matplotlib termcolor einops

pip install -e .
```

验证：

```bash
python -c "import vla_network, transformers, cv2, zmq; print('ok', transformers.__version__)"
```

### ⚠ 坑点 E

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| `opencv-python` 最新版与 `numpy==1.26.4` 冲突 | pip 反复试多个 opencv 大包，占满磁盘 | **钉死** `opencv-python==4.10.0.84` |
| torch 先装来 `numpy 2.0.x` | §E 必须显式 `numpy==1.26.4` 降回去 | 本机就是这样；让 pip 覆盖即可 |
| `transformers` 与 `huggingface_hub` 版本互顶 | `transformers==4.53.1` 需要 `huggingface_hub<1.0` | 让 pip 自动降到 0.36.x；不要强行装 hub 1.8 再跑 transformers |
| 缺 `einops` | 加载 InternLM 建模文件时报 `ModuleNotFoundError: einops` | `pip install einops`（本教程已写入） |
| `pip install -r requirements.txt` 覆盖 torch | 可能装上 CPU 版或错误 CUDA 版 | 先装 torch，再装其余依赖 |
| 装包时 turbo 仍开着 | 清华源/PyPI 极慢 | 与 §D 相同：unset 代理和 CA 变量 |

---

## F. 下载主权重（12.6GB）

⏱ **本机实测：~42 min**（`network_turbo` + curl，均速约 5 MB/s；峰值曾到 ~12 MB/s）  
**GPU：不需要。内存：curl 流式几乎不占。** 这是最长的无 GPU 步骤之一。

### F.0 为何不用 `hf download`（紧内存机必读）

本机 cgroup **2GiB** 下，直接跑：

```bash
hf download shengliangd/GraspVLA --local-dir ...
```

会在开始拉大文件后不久被 **OOM kill（exit 137）**。`huggingface_hub` 默认多 worker，再叠加已占用的 agent/环境内存，很容易顶满 2GiB。  
**对策：** 用 `curl -L -C -` 流式写入目标文件（支持断点续传）。内存充裕（例如 ≥8GiB 可用）时仍可用官方 `hf download`。

### F.1 推荐：curl 下载（本机采用）

```bash
source /etc/network_turbo
unset HF_ENDPOINT   # 走官方 huggingface.co

export GRASPVLA_ROOT=/root/autodl-tmp/GraspVLA_repro
OUT="$GRASPVLA_ROOT/weights/checkpoint/model.safetensors"
mkdir -p "$(dirname "$OUT")"

curl -L --fail --retry 40 --retry-delay 8 \
  --connect-timeout 30 \
  -C - \
  --output "$OUT" \
  "https://huggingface.co/shengliangd/GraspVLA/resolve/main/checkpoint/model.safetensors"
```

小文件（`config.json` / `preprocessor.npz` 等）可一并拉：

```bash
for f in config.json preprocessor.npz README.md .gitattributes; do
  curl -L --fail -C - --output "$GRASPVLA_ROOT/weights/$f" \
    "https://huggingface.co/shengliangd/GraspVLA/resolve/main/$f"
done
```

验收：

```bash
ls -lh "$GRASPVLA_ROOT/weights/checkpoint/model.safetensors"
# 期望恰好 12624643076 bytes ≈ 12.62 GB
stat -c '%s' "$GRASPVLA_ROOT/weights/checkpoint/model.safetensors"
```

若曾用失败的 `hf download` 留下 `weights/.cache`，确认正式文件完整后可删：

```bash
rm -rf "$GRASPVLA_ROOT/weights/.cache"
df -h /root/autodl-tmp
```

### F.2 备选：内存充足时用 `hf download`

```bash
source /etc/network_turbo   # 或：export HF_ENDPOINT=https://hf-mirror.com
pip install -U "huggingface_hub<1.0"   # 与 transformers 4.53 兼容；仅下载也可用更新版
hf download shengliangd/GraspVLA --local-dir "$GRASPVLA_ROOT/weights" --max-workers 1
```

### ⚠ 坑点 F

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| `hf download` exit 137 | 大文件刚开始就死 | cgroup 内存紧；改用 curl（§F.1） |
| 直连 `huggingface.co` 极慢/超时 | 长时间 0% | AutoDL：`source /etc/network_turbo`；否则 `HF_ENDPOINT=https://hf-mirror.com`（不要叠） |
| turbo 开着去装 pip | 权重下得快、随后装 torch 极慢 | 下载完立刻 unset 代理和 CA 变量 |
| 下完后 `.cache` 与正式文件双倍占盘 | 数据盘只剩个位数 GB | 确认 `model.safetensors` 完整后删 `weights/.cache` |
| 中断后续传 | 有半截文件 | curl 同一条命令加 `-C -` 即可续传 |
| 百度网盘备选 | 公司网络禁 HF | 官方 README 有百度链接；密码见项目页 |

官方权重页：[shengliangd/GraspVLA](https://huggingface.co/shengliangd/GraspVLA)

---

## G. 启动 Model Server（端口 **6006**）

### G.1 首次启动会发生什么（非常重要）

⏱ **本机首次（未预下载骨干）：~60–75 min**（绝大部分时间在静默下载骨干）  
⏱ **本机再次 / 已按 §G.1.1 预下载：~2–5 min**（加载权重 + warmup）——**本机按此计，warmup 后约 2.0 it/s**  
**GPU：下载骨干不需要；加载、warmup、监听端口需要（约 10GB 显存）。**

`serve` **不只是加载你下的 12.6GB**。代码里还会用 `timm` / `transformers` 拉：

| 骨干 | 约体积 | 用途 |
| --- | --- | --- |
| `timm/vit_large_patch14_reg4_dinov2.lvd142m` | ~1.22 GB | 视觉 DINO |
| `timm/vit_so400m_patch14_siglip_224.v2_webli` | ~1.71 GB | 视觉 SigLIP |
| `internlm/internlm2-1_8b` | ~3.8 GB | LLM 骨架初始化 |

这些都进 `$HF_HOME`。日志在下载阶段可能**几乎只有一行 FutureWarning**，看起来像死机——其实在写 `.incomplete` 文件。

### G.1.1 无 GPU 预下载三块骨干（推荐，避免租卡空等）

⏱ **本机实测：~23 min**（turbo + curl 写入 hub；跳过与 safetensors 重复的 `pytorch_model.bin`）  
**GPU：不需要。** 只往磁盘写缓存；做完再开 GPU 跑 §G.2。

`serve` / `timm` / `transformers` 默认读 **`$HF_HOME/hub/models--*`** 布局。紧内存下不要用 `hf download`（易 137），用本教程脚本把文件 curl 进同一布局：

```bash
source /etc/network_turbo
unset HF_ENDPOINT

export GRASPVLA_ROOT=/root/autodl-tmp/GraspVLA_repro
export HF_HOME="$GRASPVLA_ROOT/hf_home"
mkdir -p "$HF_HOME/hub"

# 脚本：GraspVLA_repro/scripts/hf_hub_curl_download.py
# - 写 blobs/ + snapshots/ + refs/main（与 huggingface_hub 兼容）
# - 若同时存在 model.safetensors 与 pytorch_model.bin，只下 safetensors（省 ~3GB）
python -u "$GRASPVLA_ROOT/scripts/hf_hub_curl_download.py" "$HF_HOME" \
  timm/vit_large_patch14_reg4_dinov2.lvd142m \
  timm/vit_so400m_patch14_siglip_224.v2_webli \
  internlm/internlm2-1_8b
```

说明：代码里 `timm.create_model("vit_so400m_patch14_siglip_224", pretrained=True)` **未写死 tag**；较新 `timm` 默认权重为 **`.v2_webli`**（本机按此预下载）。若日后 serve 仍去拉 `.webli`，再补下 `timm/vit_so400m_patch14_siglip_224.webli` 即可。

**跳过 `pytorch_model.bin` 的后果：** 省约 3GB，但 **不能** 再设 `HF_HUB_OFFLINE=1`——timm 离线时会硬找 bin，不会自动用旁边的 safetensors。缓存齐后的启动方式见 §G.2（hf-mirror HEAD）。

验收：

```bash
du -sh "$HF_HOME/hub/models--timm--vit_large_patch14_reg4_dinov2.lvd142m" \
       "$HF_HOME/hub/models--timm--vit_so400m_patch14_siglip_224.v2_webli" \
       "$HF_HOME/hub/models--internlm--internlm2-1_8b"
# 本机约：1.2G / 1.6G / 3.6G；不应再有 .part / .incomplete
find "$HF_HOME" \( -name '*.incomplete' -o -name '*.part' \)
```

**内存充裕时的等价写法**（勿与 2GiB cgroup 混用）：

```bash
export HF_HOME="$GRASPVLA_ROOT/hf_home"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
hf download timm/vit_large_patch14_reg4_dinov2.lvd142m --max-workers 1
hf download timm/vit_so400m_patch14_siglip_224.v2_webli --max-workers 1
hf download internlm/internlm2-1_8b --max-workers 1
```

不要设 `TRANSFORMERS_CACHE`（见坑点 G）。

### G.2 启动命令（本教程端口 6006）

**终端 A：**

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"

# 关 turbo：缓存已齐，不需要代理；turbo 的 CA 变量会干扰直连
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
unset REQUESTS_CA_BUNDLE SSL_CERT_FILE
unset OMP_NUM_THREADS
# 不要设 HF_HUB_OFFLINE / TRANSFORMERS_OFFLINE（见坑点 G）

export HF_HOME="$GRASPVLA_ROOT/hf_home"
export HUGGINGFACE_HUB_CACHE="$HF_HOME/hub"
# 无 turbo 时 huggingface.co 可能不通；mirror 只做 HEAD，权重仍走本地 safetensors
export HF_ENDPOINT=https://hf-mirror.com
# 不要 export TRANSFORMERS_CACHE

cd "$GRASPVLA_CODE"
MODEL="$GRASPVLA_ROOT/weights/checkpoint/model.safetensors"

python3 -u -m vla_network.scripts.serve \
  --path "$MODEL" \
  --port 6006 \
  2>&1 | tee "$GRASPVLA_ROOT/logs/serve_6006.log"
```

### G.3 如何判断“没卡死”（另开终端监控）

```bash
# 1) 骨干是否还在下
find "$HF_HOME" -name '*.incomplete' -printf '%s %p\n' 2>/dev/null
du -sh "$HF_HOME"

# 2) 显存是否开始涨（加载到 GPU 后会从 ~0 跳到 ~10GB）
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv

# 3) 日志
tail -f "$GRASPVLA_ROOT/logs/serve_6006.log"
```

### G.4 成功标志（按出现顺序）

1. （可选）`Flex Attention not implemented, use pytorch version instead` → **可忽略**
2. （可选）`The new embeddings will be initialized...` → **可忽略**（扩词表提示）
3. `warming up...`（tqdm 跑 5 次）
4. `check the latency after warm up:`（再跑 5 次，本机约 **2.0 it/s**）
5. **`Started server on port 6006`** ← 到这一行才算真正就绪

### G.5 可选：`--compile` 加速推理

```bash
python3 -u -m vla_network.scripts.serve --path "$MODEL" --port 6006 --compile
```

- 好处：官方称可从 ~500ms → ~200ms  
- 代价：启动多约 **~3 min** 编译  
- 适合：大规模评测；本地快速验收可不加

### ⚠ 坑点 G

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| **日志长时间无新输出** | 误以为进程挂了 | 看 `.incomplete` 体积是否增长；InternLM 单文件约 3.8GB，网速 1–2MB/s 时要半小时+ |
| `HF_HOME` 落在系统盘 `~/.cache/huggingface` | `/` 被骨干下载撑满 | 启动前必须 `export HF_HOME=数据盘路径` |
| **关 turbo 后 HF 官方不通** | serve 又去拉骨干 / 卡住 | 缓存已齐时不要开 turbo；设 `HF_ENDPOINT=https://hf-mirror.com` 只做连通性 HEAD |
| **`HF_HUB_OFFLINE=1` 卡死** | 日志停在找 `pytorch_model.bin` | §G.1.1 **故意跳过了**与 safetensors 重复的 bin。离线模式不会回退到本地 `model.safetensors`。**不要纯离线**，用 hf-mirror HEAD + 本地缓存 |
| **`TRANSFORMERS_CACHE` 与 `HF_HOME/hub` 分裂** | 完整 InternLM 在 `hf_home/models--*`，进程却往 `hf_home/hub/models--*` 重下 | **不要**设 `TRANSFORMERS_CACHE`；只设 `HF_HOME` + `HUGGINGFACE_HUB_CACHE=$HF_HOME/hub` |
| turbo 与 hf-mirror 叠用 | 更慢或证书错误 | 二者择一；serve 阶段用 mirror、关 turbo |
| `OMP_NUM_THREADS` Invalid value | `libgomp: Invalid value...` | `unset OMP_NUM_THREADS` |
| 端口被占 | `Address already in use` | `pkill -f vla_network.scripts.serve` 后换端口，或 `ss -ltnp \| grep 6006` |
| Flex Attention 警告 | 看起来像错误 | 警告可忽略，代码会退回普通 PyTorch attention |
| embeddings / lm_head mean_resizing 提示 | 扩词表警告 | **可忽略** |
| 第一次把 `HF_HOME` 指错后又改对 | 半截下载留在旧目录 | 把旧 `~/.cache/huggingface` 挪到新 `HF_HOME`，或删掉重下 |
| serve 脚本注释写 `import urchin` | 本仓库推理路径实际未强制 urchin | 离线 server **不必**装 urchin |

---

## H. 离线验收：`offline_test`（对接 6006）

⏱ **本机实测：~5–10 s**（含一次校验请求 + 一次真实样例推理）  
**GPU：客户端脚本几乎不占卡；必须已有 GPU 上的 Model Server。** 无 GPU 无法完成这一验收。

**终端 B（服务保持运行）：**

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate "$GRASPVLA_ROOT/env"
cd "$GRASPVLA_CODE"

python3 -u -m vla_network.scripts.offline_test --port 6006
```

### 期望输出

```text
✓ Server at 127.0.0.1:6006 returned valid dict
Task: pick up pen
Saved figure as "visualization/trial-20250507120350_visualization.png".
```

### 看图

```bash
ls -lh "$GRASPVLA_CODE/visualization/trial-20250507120350_visualization.png"
# 左：官方参考；右：你当前 6006 服务的输出（bbox 可视化）
```

本机实测对比图（副本也在 `$GRASPVLA_ROOT/visualization/`）：

![本机 offline_test 对比图（左：官方参考；右：6006 服务输出）](visualization/trial-20250507120350_visualization.png)

*图：本机 `offline_test --port 6006` 结果。左为官方参考（Our Result），右为当前 6006 服务输出（Your Result）。两路视角绿框都框在红笔上，与参考一致。*

服务端日志本机为 4 次请求（含校验 + 样例），约 **0.47–0.54 s/次**：

```text
Started server on port 6006
start processing a request
finished a request in 0.486s
...
finished a request in 0.508s
```

### ⚠ 坑点 H

| 坑 | 现象 | 解决 |
| --- | --- | --- |
| 端口写错 | `✗ Server ... timeout` | 与 serve 的 `--port` 一致，本教程为 **6006** |
| 服务还在 warmup | timeout | 等到日志出现 `Started server on port 6006` 再测 |
| 工作目录不对 | 找不到 `visualization/*.npy` | 必须在仓库根目录 `$GRASPVLA_CODE` 下执行 |
| 无显示环境 | matplotlib 仍可 `savefig` | 服务器上一般没问题；不要依赖 `plt.show()` |
| 图已生成但教程相对路径找不到 | md 在 `/root/autodl-tmp/`，png 默认写在仓库 `visualization/` | `cp` 一份到 `$GRASPVLA_ROOT/visualization/` 与教程旁 `visualization/` |
| 把 bbox 一致当成 LIBERO/真机复现 | 过度解读 | 本验收只证明 **指令 → 感知框 + 动作** 链路；见文首边界 |

---

## I. 日常启停（缓存已齐后的最短路径）

⏱ **约 2–5 min 启动 + 数秒测试**  
**GPU：需要。** 权重与骨干已在磁盘上时，不应再出现长时间“无日志”；若又开始写 `.incomplete`，说明 `HF_HOME`/`hub` 又指错了（回到无 GPU 可修的下载问题）。

```bash
# ===== 终端 A：启动（6006）=====
source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/GraspVLA_repro/env
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
unset REQUESTS_CA_BUNDLE SSL_CERT_FILE OMP_NUM_THREADS
export HF_HOME=/root/autodl-tmp/GraspVLA_repro/hf_home
export HUGGINGFACE_HUB_CACHE=$HF_HOME/hub
export HF_ENDPOINT=https://hf-mirror.com
cd /root/autodl-tmp/report/repos/GraspVLA

python3 -u -m vla_network.scripts.serve \
  --path /root/autodl-tmp/GraspVLA_repro/weights/checkpoint/model.safetensors \
  --port 6006 \
  2>&1 | tee /root/autodl-tmp/GraspVLA_repro/logs/serve_6006.log

# ===== 终端 B：验收 =====
source /root/miniconda3/etc/profile.d/conda.sh
conda activate /root/autodl-tmp/GraspVLA_repro/env
cd /root/autodl-tmp/report/repos/GraspVLA
python3 -u -m vla_network.scripts.offline_test --port 6006
```

停止服务：

```bash
pkill -f 'vla_network.scripts.serve'
# 确认显存释放
nvidia-smi
```

---

## J. 完整踩坑速查表（按两阶段实测）

### 无 GPU 阶段（下载）

1. **磁盘分盘失败** → 环境放系统盘，权重/`HF_HOME` 放数据盘；串行下载与安装。  
1a. **GPU 空转干等下载** → 主权重与 DINO/SigLIP/InternLM 均可无 GPU 预下载。  
1b. **cgroup 内存只有 2GiB** → `free -h` 不可信；`hf download` 易 exit 137；改用 curl / `scripts/hf_hub_curl_download.py`。  
1c. **AutoDL 网络分流** → `source /etc/network_turbo` **只**加速 GitHub/HF；装 pip/conda/torch **必须** `unset` 代理，并清掉 `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE`。  
1d. **turbo + `HF_ENDPOINT=hf-mirror` 叠用** → 更慢或乱源；下载阶段二选一（本机下载用 turbo 直连官方）。  
2. **conda `pkgs/free` 频道 404** → `--override-channels` + tuna main + defaults。  
3. **timm 同时下 safetensors+bin** → 预下载跳过重复的 `pytorch_model.bin`，省约 3GB（serve 阶段不要因此开 `HF_HUB_OFFLINE`，见下）。

### GPU 阶段（安装 + serve）— 本机新增

4. **torch 安装撑爆 `/`** → 先清 `/root/.cache/pip` 与 `/tmp/pip-unpack-*`；`/` 仍紧则 `TMPDIR` 改数据盘。  
5. **`download.pytorch.org` 大文件超时** → pip 下 ~1GB 的 torch 主包反复 `Connection timed out`。**不是 5090 不能用 cu128。** 改 `curl -C -` 到 `$GRASPVLA_ROOT/tmp/wheels`，再 `pip install --no-deps` 三个本地 wheel（§D.3）。  
6. **`--no-index --find-links=$PIP_CACHE_DIR` 失败** → 报 `No matching distribution found for filelock`。pip 的 http-v2 缓存 **不是** 平铺 wheel 目录，`--find-links` 扫不到。把 `*.whl` 摊平，或不要 `--no-index`。  
7. **本地已有 triton，pip 又去网上拉** → 只把 torch/torchvision 当本地路径时，依赖解析仍会下 triton。三个 wheel 都传本地，或 `--no-deps`。  
8. **`files.pythonhosted.org` / 清华源 pip 极慢** → pillow 超时；tuna 可到 ~35KB/s。同一 URL 用 curl 落到数据盘再 `--no-index` 安装。  
9. **opencv 与 numpy 打架** → `opencv-python==4.10.0.84` + `numpy==1.26.4`（torch 可能先装来 numpy 2.x，§E 再钉回去）。  
10. **关 turbo 后 HF 官方不通** → serve 不要开 turbo；`export HF_ENDPOINT=https://hf-mirror.com` 做 HEAD。  
11. **`HF_HUB_OFFLINE=1` 卡在 `pytorch_model.bin`** → 预下载只留了 safetensors。用 hf-mirror HEAD + 本地缓存，**不要**纯离线。  
12. **`TRANSFORMERS_CACHE` 与 `HF_HOME/hub` 分裂** → 不要设前者；只设 `HF_HOME` 与 `HUGGINGFACE_HUB_CACHE=$HF_HOME/hub`。  
13. **首次 serve「假死」** → 其实在下骨干；盯 `.incomplete`。缓存齐后 2–5 min 应到 `Started server on port 6006`。  
14. **OMP 告警** → `unset OMP_NUM_THREADS`。  
15. **端口不一致** → serve 与 offline_test 都用 **6006**。

### 一句话对照

| 阶段目标 | 真正容易卡死的点 | 不要误判成 |
| --- | --- | --- |
| 无 GPU 下载 | 2GiB cgroup + `hf download` OOM；系统盘太小 | 「没 GPU 就做不了」 |
| GPU 装 torch | pytorch.org 大文件超时 + 本地缓存用法错 | 「cu128 / 5090 不兼容」 |
| GPU 起 serve | 关 turbo 后 HF 不通；离线模式要 bin | 「权重没下完 / 模型坏了」 |

---

## K. 本教程不覆盖 / 下一步

| 方向 | 仓库 | 额外成本 |
| --- | --- | --- |
| LIBERO / 仿真 playground | [GraspVLA-playground](https://github.com/MiYanDoris/GraspVLA-playground) | 仿真依赖、更多磁盘与时间 |
| 真机控制 | [GraspVLA-real-world-controller](https://github.com/MiYanDoris/GraspVLA-real-world-controller) | 双目/腕部相机、机械臂、标定 |
| 从头训练 SynGrasp-1B | 官方尚未在本仓库给出完整 train 脚本入口 | 数据与算力远超本教程范围 |

二者都假设你已经有一个可用的 **ZMQ Model Server**（本教程的 6006）。

---

## L. 引用

```bibtex
@article{deng2025graspvla,
    title={GraspVLA: a Grasping Foundation Model Pre-trained on Billion-scale Synthetic Action Data},
    author={Shengliang Deng and Mi Yan and Songlin Wei and Haixin Ma and Yuxin Yang and Jiayi Chen and Zhiqi Zhang and Taoyu Yang and Xuheng Zhang and Wenhao Zhang and Heming Cui and Zhizheng Zhang and He Wang},
    year={2025},
    eprint={2505.03233},
    archivePrefix={arXiv},
    primaryClass={cs.RO},
    url={https://arxiv.org/abs/2505.03233}
}
```
