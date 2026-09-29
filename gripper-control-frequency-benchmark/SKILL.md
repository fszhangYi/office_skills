---
name: gripper-control-frequency-benchmark
description: >-
  Benchmark electric gripper control frequency and motion speed with four
  isolated test scripts: sync command frequency, async command frequency,
  status read frequency, and fastest open-close round-trip. Use when the user
  asks to measure gripper Hz, control bandwidth, Modbus loop rate, async vs
  sync command rate, acquisition/read rate, or fastest open/close time. Assumes
  a user-provided base SDK; if none is given, recommend constructing the SDK
  after zefg_c65.py.
---

# Gripper Control Frequency Benchmark

为电动夹爪生成并运行**与基础驱动隔离**的四项测速脚本，输出脚本与实测结果。

## Hard rules

1. **不要把测速逻辑写进驱动**。驱动只提供连接、读写、运动 API；四个脚本各自 `import` 驱动，驱动不得反向依赖脚本。
2. **用户提供基础 SDK 时**：只适配脚本的 import 与调用面，不要重写驱动内部协议。
3. **用户未指定 SDK 时**：按 [ref/SDK_CONTRACT.md](ref/SDK_CONTRACT.md) 与仓库中的 `zefg_c65.py` 给出构造建议（或提示复制该驱动），再写四个测速脚本。
4. **交付物必须齐全**：四个脚本 + 各自 CSV/控制台结果摘要。脚本模板与说明见 [ref/](ref/USAGE.md)。

## Four tests

| 名称 | 参考脚本 | 结果文件 | 测什么 |
| --- | --- | --- | --- |
| 同步控制频率 | [ref/scripts/response_frequency_test.py](ref/scripts/response_frequency_test.py) | [ref/results/frequency_test_result.csv](ref/results/frequency_test_result.csv) | 每拍「写位置+读反馈」回路 Hz；小方波跟踪到 -3 dB |
| 异步控制频率 | [ref/scripts/async_frequency_test.py](ref/scripts/async_frequency_test.py) | [ref/results/async_frequency_test_result.csv](ref/results/async_frequency_test_result.csv) | 只写位置的指令 Hz；另一线程采样反馈做跟踪扫频 |
| 采集/读取频率 | [ref/scripts/read_frequency_test.py](ref/scripts/read_frequency_test.py) | [ref/results/read_frequency_test_result.csv](ref/results/read_frequency_test_result.csv) | 连续 `read_status` / 寄存器读 Hz，夹爪不动 |
| 最快开合速度 | [ref/scripts/reciprocate_time_test.py](ref/scripts/reciprocate_time_test.py) | [ref/results/reciprocate_time_test_result.csv](ref/results/reciprocate_time_test_result.csv) | 满行程张开+闭合往复最短耗时 |

使用说明、命令行、默认参数与解读： [ref/USAGE.md](ref/USAGE.md)。

## Workflow

复制清单并跟踪：

```
- [ ] 1. 确认基础 SDK 路径与端口
- [ ] 2. 核对 SDK 满足 ref/SDK_CONTRACT.md
- [ ] 3. 从 ref/scripts 复制/适配四个脚本到工作目录（勿内置进驱动）
- [ ] 4. 依次运行四项测试并保存 CSV
- [ ] 5. 向用户汇报四项关键指标 + 结果文件路径
```

### Step 1 — SDK

- 用户指定了模块/类：记录 `import` 路径、串口、从站 ID、行程上限。
- 未指定：建议基于 `zefg_c65.py` 构造，最小面见 [ref/SDK_CONTRACT.md](ref/SDK_CONTRACT.md)。

### Step 2 — Adapt scripts

1. 复制 `ref/scripts/*.py` 到项目（可改名，但保持四项语义）。
2. 把 `from zefg_c65 import ...` 换成用户 SDK；保持测速逻辑与驱动分离。
3. 异步脚本可继续依赖同步脚本中的 `FREQUENCIES_HZ` / `crossing` / `wait_reached`，或把公共工具抽到独立 `benchmark_common.py`（仍不要放进驱动）。
4. 行程、速度、电流默认与参考一致：中位方波约 `32±4 mm`，速度 `100 mm/s`，电流上限；满行程开合用 `0 ↔ stroke_max`。

### Step 3 — Run

在目标机、夹爪已上电且行程畅通时运行（详见 USAGE）。优先实机跑出 CSV；无法实机则交付脚本并说明未测原因。

### Step 4 — Report

向用户报告至少：

1. **同步回路 Hz** 与 **-3 dB 跟踪频率**
2. **异步只写 Hz** 与 **异步 -3 dB 跟踪频率**（注明采样 Hz；高频跟踪比回升可能是混叠）
3. **状态帧读取 Hz**（及单寄存器对照）
4. **最快往复耗时**（张开/闭合分段 + 往复合计）

附参考实测量级（Z-EFG-C65 @ COM3, 115200）：见 [ref/results/](ref/results/) 与 USAGE 中的摘要表。

## Isolation checklist

- [ ] 驱动文件无 `import` 四个测速脚本
- [ ] 四个脚本只通过公开 API 调驱动
- [ ] 结果 CSV 写在测试目录，不写入驱动包内部
- [ ] 改测速参数不需要改驱动源码
