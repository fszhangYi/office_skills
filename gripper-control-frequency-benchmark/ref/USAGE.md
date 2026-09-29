# 参考脚本与使用说明

本目录脚本针对 **Z-EFG-C65 + `zefg_c65.py`** 实机验证过。换夹爪/SDK 时保留测法，替换 import 与行程参数。

## 文件一览

| 脚本 | 作用 | 默认输出 CSV |
| --- | --- | --- |
| [scripts/response_frequency_test.py](scripts/response_frequency_test.py) | 同步控制频率 | `frequency_test_result.csv` |
| [scripts/async_frequency_test.py](scripts/async_frequency_test.py) | 异步控制频率 | `async_frequency_test_result.csv` |
| [scripts/read_frequency_test.py](scripts/read_frequency_test.py) | 数据读取/采集频率 | `read_frequency_test_result.csv` |
| [scripts/reciprocate_time_test.py](scripts/reciprocate_time_test.py) | 最快满行程开合 | `reciprocate_time_test_result.csv` |

参考结果样本：[results/](results/)。

依赖：`pyserial`；Python 3.10+ 推荐。异步测试依赖同步脚本中的公共符号（或抽公共模块）。

## 前置条件

1. 夹爪 24V 功率充足；GND 与 USB-RS485 共地。
2. 串口空闲（如 `COM3`），驱动可 `status` 读通。
3. 初始化完成（状态码 5 / `initialized`）。
4. 扫频与往复时手指行程内无障碍；往复用最大速度/电流前确认安全。

## 运行命令

在含驱动与脚本的工作目录：

```bash
python response_frequency_test.py --port COM3
python async_frequency_test.py --port COM3 --sample-hz 25
python read_frequency_test.py --port COM3 --seconds 3
python reciprocate_time_test.py --port COM3 --cycles 5
```

常用参数：

- `--center` / `--amplitude`：同步/异步方波中心与单侧幅度（mm）
- `--speed` / `--current`：mm/s 与 A
- `--sample-hz`：异步反馈采样率
- `--cycles`：往复次数

## 指标怎么读

### 1. 同步控制频率

- **同步回路 Hz**：同一位置反复 `set_position` + `read_status`，测总线往返上限。
- **方波跟踪比**：反馈峰峰值 / 指令峰峰值；**-3 dB** = 跟踪比跌破 0.707 的插值频率。
- 运动学粗略上限：`speed / (4 * amplitude)`（忽略加减速）。

参考样本（32±4 mm，100 mm/s，0.5 A）：同步回路约 **31.3 Hz**，-3 dB 约 **7.4 Hz**。

### 2. 异步控制频率

- **异步指令 Hz**：只写位置、不读反馈。
- 扫频时写线程与读线程抢半双工总线，实际写速会低于纯写基准。
- 高频段跟踪比异常回升时，优先怀疑**采样混叠**，不要当成机械带宽提升。

参考样本：纯写约 **62.5 Hz**；扫频时指令约 38 Hz；-3 dB 约 **4.4 Hz**（采样 25 Hz）。

### 3. 采集/读取频率

- 夹爪不动，连续读状态帧（及可选短帧对照）。
- 主指标：状态帧 Hz 与平均周期 ms。

参考样本：8 寄存器状态帧约 **62.5 Hz**（≈16 ms）；缩短寄存器数未必更快。

### 4. 最快开合速度

- 满行程 `0 ↔ stroke_max`，最大速度/电流。
- 单程：发位置指令起，到进入目标容差且非运动中。
- 往复 = 张开 + 闭合；报告最块一次与平均。

参考样本（0↔65 mm，100 mm/s，0.5 A，5 次）：最快往复约 **1.615 s**（张开 0.832 s + 闭合 0.784 s）。手册单向最短约 0.7 s，实测单向常略慢。

## 与驱动隔离

```
zefg_c65.py (或用户 SDK)
        ^
        |  import / 公开 API
        |
response_frequency_test.py
async_frequency_test.py  ---> 可复用同步脚本的工具函数
read_frequency_test.py
reciprocate_time_test.py
```

驱动**不得** import 上述脚本。交付时脚本与 CSV 放在测试目录即可。

## 适配检查表

- [ ] import 已指向用户 SDK 或薄适配器
- [ ] 行程上限与安全中位已按机型调整
- [ ] 四项都能生成独立 CSV
- [ ] 报告中区分「通信 Hz」与「机械跟踪 Hz」
