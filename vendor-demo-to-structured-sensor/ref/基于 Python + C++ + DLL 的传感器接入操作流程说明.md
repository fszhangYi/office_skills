## 基于 Python + C++ + DLL 的传感器接入操作流程说明

本文以触觉传感器为例，叙述了使用 python 和 c++ 联合调用获取传感器数据的一般流程。从底层驱动层层封装，结合两种编程语言实现跨语言的数据调用，极具复用性和灵活性。

---

## 1. 目标与输入

本次任务目标是把“可运行的 Python 串口采集逻辑”迁移为“标准 C++ 工程 + DLL 接口”，并让 `Touch.py` 按既有方式调用。

- `Touch.py`：最终调用 DLL 的入口文件，模板见同目录 [`使用 Python 加载 C++ 封装好的动态链接库类模板.md`](./使用%20Python%20加载%20C++%20封装好的动态链接库类模板.md)。基于该模板（文中完整参考代码），只对业务方法稍作改动即可适配当前需求。
- `Reference.py`：可成功采集数据的协议与业务参考，一般由供应商提供。
- `seal_template.py`：分层封装风格参考，见同目录 [`串口设备数据交互的三重封装.md`](./串口设备数据交互的三重封装.md)。将该文中的参考代码保存成此文件即可。
- `cpp_project_template.md`：C++ 项目组织方式参考（`include/src/build/bin/lib`），见同目录 [`linux 上编译 c++ 项目结构.md`](./linux%20上编译%20c++%20项目结构.md)。可直接将该全文作为工程模板使用。

> 使用 vibe coding 的方式，将供应商资料或者本地模板放进工作目录，保存成 `Touch.py` `Reference.py` 等文件名称。然后在大模型中输入如下的提示词：
> 在工作目录下有四个文件，其中 `Touch.py` 是最终调用 DLL 的入口文件（模板来自 `使用 Python 加载 C++ 封装好的动态链接库类模板.md`）；`Reference.py` 是供应商提供的示例代码；`seal_template.py` 是封装用的结构示例文件（来自 `串口设备数据交互的三重封装.md`）；`cpp_project_template.md` 是一个 c++ 项目模板（来自 `linux 上编译 c++ 项目结构.md`）。你需要参考 Reference.py 的实现和 seal_template.py 的格式创建符合格式的 python 程序；然后参考 cpp_project_template.md 中 c++ 项目的组织方式，将上一步的 python 程序变成一个 c++ 项目，最后参考 Touch.py 的调用方式，完善 c++ 项目的代码，然后打包得到 dll 并在 Touch.py 中引用
---

## 2. 总体实施思路

按“先对齐接口，再迁移实现，最后联调验证”的顺序推进：

1. **接口先行**：先锁定 `Touch.py` 需要的 DLL 导出函数与结构体布局  
2. **Python 封装对齐**：先用 `seal_template.py` 风格封装一份 Python 版分层实现  
3. **C++ 工程化迁移**：按 `cpp_project_template.md` 建 CMake 工程并实现同等协议逻辑  
4. **生成 DLL**：编译输出动态库并放到 `Touch.py` 默认可加载路径  
5. **端到端验证**：验证 `ctypes` 加载、函数调用、错误码回传是否正常

---

## 3. 第一步：确认 `Touch.py` 的 DLL 契约

`Touch.py` 对 DLL 的核心依赖是 3 个导出函数：

- `create_sensor_handle(void** handle, int port_hint)`
- `destroy_sensor_handle(void* handle)`
- `get_sensor_data(void* handle, DATA_NEED* output)`

同时，Python 侧 `ctypes.Structure` 的内存布局必须与 C++ 结构体严格一致：

- `RAW_DATA`
- `DATA_LAYER_1`
- `DATA_LAYER_2`
- `DATA_NEED`

这是整个流程中最关键的一步：**接口名称、参数类型、结构体字段顺序和大小必须一致**。

---

## 4. 第二步：先做 Python 分层封装（对标 `seal_template.py`）

新增了 `sealed_sensor.py`，按三层设计组织：

- **串口层**：`SerialDevice`（连接、收发、端口管理）
- **协议层**：`ProtocolDevice`（LRC 计算、命令拼包、响应解析）
- **业务层**：`MultiSensorRobot`（循环采集 CN1/CN2、线程安全观测）

实现依据来自 `Reference.py` 的命令协议，包括：

- 选择端口命令（CN1/CN2）
- 获取数据命令（`get_data/get_data2`）
- 头尾帧校验与长度域解析

这一步的价值是先把“协议行为”抽象清楚，再迁移到 C++，降低一次性迁移风险。

---

## 5. 第三步：按 `cpp_project_template.md` 组织 C++ 项目

已创建标准目录与文件：

- `CMakeLists.txt`
- `include/sensor_api.h`
- `src/sensor_core.h`
- `src/sensor_core.cpp`
- `src/sensor_api.cpp`
- `src/main.cpp`
- 构建目录：`build/`
- 产物目录：`bin/`、`lib/`

其中：

- `sensor_core.*`：负责串口与协议收发
- `sensor_api.cpp`：负责 DLL 导出接口与数据结构填充
- `main.cpp`：本地 demo 调试入口
- `sensor_api.h`：统一对外 ABI（给 Python `ctypes` 对齐）

---

## 6. 第四步：实现并导出 DLL 接口

C++ 侧通过 `extern "C"` 导出接口，避免 C++ 名字改编，确保 Python 可直接按函数名绑定。

`get_sensor_data` 的实现流程：

1. 读取 CN1 原始字节
2. 读取 CN2 原始字节
3. 填充到 `DATA_NEED.data_group[0/1]`
4. 计算并写入 `rest_data`
5. 设置 `num = 2`

这样 `Touch.py` 的 `get_data/get_force` 可以直接复用，不需改动上层业务逻辑。

---

## 7. 第五步：构建、打包、接入

### 构建命令

在 `build/` 目录执行：

- `cmake ..`
- `cmake --build .`

成功后产出：

- `bin/Debug/TouchSensor.dll`
- `lib/Debug/TouchSensor.lib`

再将 DLL 放到 Python 默认加载位置：

- `lib/TouchSensor.dll`

---

## 8. 第六步：修改 `Touch.py` 的加载策略

为便于直接运行，做了两个增强：

- 默认 DLL 路径改为：`lib/TouchSensor.dll`
- 新增参数 `com_port`（默认 `5`），传入 `create_sensor_handle`

示例：

- `handler = PaxiniHandler()`（默认 COM5）
- `handler = PaxiniHandler(com_port=8)`（指定 COM8）

---

## 9. 验证策略与结果

建议按三层验证：

1. **库加载验证**：`ctypes.CDLL` 能否成功加载 DLL  
2. **接口调用验证**：能否调用 `create_sensor_handle` 并收到合理返回码  
3. **设备联调验证**：在真实设备上获取到稳定数据帧

当前已完成前两层，设备不存在或端口不匹配时返回错误码，行为符合预期。

---

## 10. 常见问题与排查建议

- **DLL 加载失败**：先检查路径是否为 `lib/TouchSensor.dll`
- **创建句柄失败**：优先核对 COM 口号、波特率、设备占用
- **有响应但数据异常**：检查帧头尾、长度域、小端序处理是否一致
- **结构体数据错位**：复核 Python/C++ 字段顺序与类型对齐

---

## 11. 结论

通过“参考脚本提炼协议 → Python 分层封装验证 → C++ 工程化实现 → DLL 接入 `Touch.py`”的流程，可以把原始采集逻辑稳定迁移到可复用的动态库形态。  
该方案兼顾了**接口兼容性**、**工程可维护性**和**后续部署便利性**，适合作为后续传感器模块标准化接入模板。
