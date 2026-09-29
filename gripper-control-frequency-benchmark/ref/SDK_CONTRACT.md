# SDK 构造建议与调用契约

测速脚本假设有一个**基础 SDK**，而不是把 Modbus/串口细节写进测速文件。

## 用户未指定 SDK 时

1. 优先查找工作区是否已有类似 `zefg_c65.py` 的驱动。
2. 若无：建议按慧灵 Z-EFG-C65 手册实现（或复制该驱动），默认 `115200 8N1`、从站 ID `1`。
3. 驱动职责：CRC、功能码 `0x03/0x06/0x10`、浮点寄存器编解码、`initialize` / `set_position` / `read_status`。
4. **测速脚本不要复制协议实现**；只 `import` 驱动类。

## 最小 API（测速需要）

上下文管理或显式开关：

```python
with Gripper(port="COM3", slave_id=1, baudrate=115200, timeout=0.2) as g:
    ...
# 或 g.connect() / g.disconnect()
```

必需方法/属性：

| 符号 | 用途 |
| --- | --- |
| `set_position(mm: float)` | 写目标开度并开始运动 |
| `set_speed(mm_s: float)` | 写速度 |
| `set_current(a: float)` | 写电流/力相关设定 |
| `read_status()` | 返回含 `position_mm`、`moving`、`initialized` 的状态 |
| `initialize()` | 找零（可选，未初始化时调用） |
| 行程常量或参数 | 如 `POSITION_MAX_MM` / `stroke_mm`（C65 为 65） |

读取频率测试额外建议：

| 符号 | 用途 |
| --- | --- |
| `read_u16(addr)` / `read_float(addr)` | 对照单寄存器与位置浮点读速 |
| 或仅用 `read_status()` | 至少给出状态帧读取 Hz |

状态对象建议字段：

- `position_mm: float`
- `moving: bool`（或与手册一致的夹持状态码：0 到位 / 1 运动中）
- `initialized: bool`（初始化完成码为 5 时可映射）

异常：统一抛出可捕获的驱动异常（参考 `ZefgC65Error`），测速脚本统计 `errors`。

## 适配用户 SDK 时

把参考脚本中的：

```python
from zefg_c65 import ZefgC65, ZefgC65Error
```

换成用户模块，必要时写 **薄适配器**（放在测速目录，不放进驱动）：

```python
# gripper_adapter.py  — 仅测试侧
from user_sdk import UserGripper

class GripperBenchAPI:
    def __init__(self, *a, **k):
        self._g = UserGripper(*a, **k)
    def __enter__(self): ...
    def set_position(self, mm): self._g.move_to(mm)  # 示例映射
    def read_status(self): ...
```

四个测速脚本只依赖适配器公开面，保持与驱动源码隔离。

## 禁止事项

- 在驱动里内嵌扫频、往复计时、多线程异步测频
- 为了测速去改驱动默认波特率/ID（除非用户明确要求）
- 把参考 CSV 当成当前夹爪的保证指标（仅作方法与量级参考）
