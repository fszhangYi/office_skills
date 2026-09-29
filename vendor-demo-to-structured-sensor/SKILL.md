---
name: vendor-demo-to-structured-sensor
description: >-
  Convert a working vendor Python serial/sensor demo into a structured
  Python+C++/DLL project (Reference, three-layer seal, CMake, ctypes entry).
  Use when packaging supplier demos, migrating demo.py/zefg drivers to
  reusable DLL + Gripper/Sensor entry modules, or following the seal
  Python/C++/DLL sensor workflow. Requires a runnable Reference demo first.
---

# Vendor Demo → Structured Sensor Project

把**已能跑通的供应商 Python 采集/demo**，按 seal 流程迁成可复用的结构化工程：  
`Reference` → 三层封装 → CMake/C++ DLL → Python ctypes 入口。

## Hard gate（必须先有 demo）

1. **用户必须提供**可运行的基础参考脚本，形态类似 `zefg_c65.py` / `demo.py` / 供应商 `Reference.py`：
   - 能打开串口（或目标总线）
   - 能完成至少一次成功读写（读状态或收一帧）
   - 协议常量、寄存器/帧格式可从代码或手册核对
2. **若用户没有提供**：
   - **立即停止生成 C++/DLL/工程骨架**
   - 明确提示用户先准备一个基础 `demo.py`（或把供应商 demo 放到工作区并给出路径）
   - 可给出最小 `demo.py` 清单（见下），等用户补齐并确认跑通后再继续
3. 不要用「空壳假协议」冒充 Reference；没有实机验证过的 demo 不得当作 Reference。

### 没有 demo 时对用户说的话（原意保留）

> 请先准备一个可运行的基础 `demo.py`（或类似 `zefg_c65.py` 的供应商参考脚本）：能打开正确串口、完成至少一次成功通信。把它放到工作目录并告诉我路径后，再继续结构化封装。

### 最小 demo 验收清单

- [ ] 串口/设备路径正确，能 `open`
- [ ] 至少一次读成功（状态/数据帧）
- [ ] 关键命令或关键寄存器地址写在代码常量里
- [ ] 用户确认本机已跑通（贴一段输出更好）

---

## 必读参考（本 skill 的 ref）

开始迁移前**阅读**这些文件（均在 [ref/](ref/)）：

| 文件 | 用途 |
| --- | --- |
| [ref/基于 Python + C++ + DLL 的传感器接入操作流程说明.md](ref/基于%20Python%20+%20C++%20+%20DLL%20的传感器接入操作流程说明.md) | 总流程与提示词 |
| [ref/使用 Python 加载 C++ 封装好的动态链接库类模板.md](ref/使用%20Python%20加载%20C++%20封装好的动态链接库类模板.md) | ctypes 需求侧模板（入口类） |
| [ref/串口设备数据交互的三重封装.md](ref/串口设备数据交互的三重封装.md) | Serial / Protocol / Robot 三层 |
| [ref/linux 上编译 c++ 项目结构.md](ref/linux%20上编译%20c++%20项目结构.md) | `include/src/build/bin/lib` + CMake |

流程说明里的引用已指向上述本地 ref；以流程说明为主线，其余三篇为模板正文。

---

## 标准产出目录

在用户指定的包目录（如 `./huiling`）生成：

```
<pkg>/
├── Reference.py           # 供应商可运行参考（用户 demo 复制/整理，勿塞测速逻辑）
├── seal_template.py       # 三层风格模板（对标三重封装，协议改成 Reference）
├── sealed_sensor.py       # 可运行分层实现
├── <Entry>.py             # ctypes 需求侧（命名用业务语义，禁止误用 Touch 套在非触觉设备上）
├── CMakeLists.txt
├── include/*_api.h        # 对外 ABI，与 Entry.py Structure 严格一致（_pack_=1）
├── src/*_core.*           # 串口/协议
├── src/*_api.cpp          # DLL 导出
├── src/main.cpp           # demo
├── lib/<LibName>.dll
├── bin/
└── README.md
```

### 命名规则

- 入口/DLL/类名用**设备真实语义**（夹爪 → `Gripper.py` / `HuilingGripper.dll` / `GripperHandler`）。
- seal 文中的 `Touch.py`、`PaxiniHandler`、`TouchSensor.dll` 仅作模板；**不要**原样套到无关设备。
- 导出函数可保留「create/destroy/get_*_handle/data」形态，前缀按设备改（如 `create_gripper_handle`）。

---

## Workflow

复制清单并跟踪：

```
- [ ] 0. 确认 Reference/demo 存在且用户声明已跑通；否则停并索要 demo.py
- [ ] 1. 读 ref 四篇 + 用户 Reference，锁定 ABI（结构体 + 3 个导出函数）
- [ ] 2. 写 seal_template.py / sealed_sensor.py（协议只来自 Reference）
- [ ] 3. 按 CMake 模板建 C++ 工程并实现同等协议
- [ ] 4. 编译 DLL 到 lib/，写 <Entry>.py ctypes 加载
- [ ] 5. 实机冒烟：读状态 + 至少一项控制/运动或采集；写 README
```

### Step 0 — Reference

- 复制用户 demo → `Reference.py`（可加头注释标明来源）。
- 测速、录制、相机等**不要**写进驱动/Reference。

### Step 1 — ABI 先行

对照 [ctypes 模板](ref/使用%20Python%20加载%20C++%20封装好的动态链接库类模板.md)：

- 3 个导出：`create_*_handle` / `destroy_*_handle` / `get_*_data`
- C++ `#pragma pack(1)` 与 Python `Structure._pack_ = 1` 一致
- 字段语义写进头文件注释与 Entry 文档（位置/力/原始字节等按设备映射）

### Step 2 — Python 分层

对照 [三重封装](ref/串口设备数据交互的三重封装.md)：

- 串口层：尽量固定复用
- 协议层：按 Reference **重写**
- 业务层：线程/观测可复用结构

先让 `sealed_sensor.py` 在无 DLL 时也能读通设备。

### Step 3 — C++ / CMake

对照 [项目结构](ref/linux%20上编译%20c++%20项目结构.md) 与流程说明第 5–7 步：

- `core` = 通信+协议；`api` = DLL 填充结构体
- Windows 路径含中文时，用 ASCII 构建目录或提供 `build_dll.bat`
- 附带 MinGW 运行库（若用 MinGW）到 `lib/`

### Step 4 — 验证

建议三层：库加载 → 创建句柄 → 实机数据。  
控制类设备再测开合/写设定等关键命令。输出简短测试报告或 `run_full_test.py`。

---

## 给大模型的工作提示词（来自流程说明，可原样使用）

在工作目录放入四个输入后：

> 在工作目录下有四个文件，其中入口 py 是最终调用 DLL 的文件（模板来自「使用 Python 加载 C++ 封装好的动态链接库类模板」）；`Reference.py` 是供应商提供的示例代码；`seal_template.py` 是封装用的结构示例（来自「串口设备数据交互的三重封装」）；`cpp_project_template.md` 是 c++ 项目模板（来自「linux 上编译 c++ 项目结构」）。你需要参考 Reference.py 的实现和 seal_template.py 的格式创建符合格式的 python 程序；然后参考 cpp_project_template.md 中 c++ 项目的组织方式，将上一步的 python 程序变成一个 c++ 项目，最后参考入口 py 的调用方式，完善 c++ 项目的代码，然后打包得到 dll 并在入口 py 中引用。

**执行本 skill 时**：若缺 `Reference.py`，不要执行上述提示词，先走 Hard gate。

---

## 反例

- 用户只说「按 seal 封装」但没有 demo → 停，要 `demo.py`
- 把测频脚本、相机预览写进 DLL/Reference
- 夹爪工程仍命名 Touch/Paxini
- Python/C++ 结构体字段顺序不一致导致错位
