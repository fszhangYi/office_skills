# 使用 Python 加载 C++ 封装好的动态链接库类模板
**需要额外注意的是！！将此模板作为完全的需求侧，那么可以在签名及数据结构定义的时候要求 DLL 的功能，也就是说 DLL 必须实现 此模板 预设的需求，从而实现了开发层面的解耦，所达成的目的就是 DLL 的提供方看到 此模板+业务改动之后 之后就能够秒懂需求**
## 0. 定义 C++ 中需要用的数据结构

在与 C++ 动态库交互时，首先需要定义与 C++ 结构体对应的 Python 类。通常使用 `ctypes.Structure` 来描述这些结构体，确保内存布局一致。

```python
from ctypes import Structure, c_float, c_ubyte, c_int, POINTER, c_void_p
import ctypes

class RAW_DATA(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("z", c_float)
    ]

class DATA_LAYER_1(Structure):
    _fields_ = [
        ("x", ctypes.c_ubyte),
        ("y", ctypes.c_ubyte),
        ("z", ctypes.c_ubyte)
    ]

class DATA_LAYER_2(Structure):
    _fields_ = [
        ("ori_data", DATA_LAYER_1 * 60),      
        ("comp_data", RAW_DATA * 60),
        ("rest_data", RAW_DATA)
    ]

class DATA_NEED(Structure):
    _fields_ = [
        ("data_group", DATA_LAYER_2 * 10),
        ("num", c_int)
    ]
```

## 1. 模板类的组成部分

该类封装了 DLL 的加载、句柄管理、数据获取以及性能测试等通用功能。主要包含以下部分：

1. 单例模式 `_instance` 和 `__new__`
2. 初始化：链接 DLL、设置函数签名、创建句柄、初始化句柄
3. 签名方法（`_setup_prototypes`）
4. 初始化句柄方法（`_init_handle`）
5. `__enter__` / `__exit__` 上下文管理器
6. `__del__` 析构方法
7. `release` 显式释放资源
8. `benchmark` 压测方法
9. `_analyze_timings` 计时分析
10. 压测结果打印方法 `print_benchmark_result`
11. 静态方法 `is_port_available`（判断串口可用性）
12. 业务相关方法 `get_data`、`get_force`

## 2. 创建单例（可选）

如果希望全局只有一个实例，可以通过 `__new__` 实现单例模式。本例未强制使用，但可以按需添加：

```python
class SensorHandler:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

## 3. 初始化

初始化过程中完成 DLL 加载、函数签名、句柄创建等操作。

```python
def __init__(self):
    self._lib = ctypes.CDLL(dll_path)  # 加载 DLL
    self._setup_prototypes()      # 设置函数签名
    self._handle = c_void_p()     # 句柄变量
    self._init_handle()           # 创建并初始化句柄
    self._data_buffer = DATA_NEED()  # 复用缓冲区，减少分配
```

## 4. 签名方法

签名方法用于告诉 `ctypes` 函数参数和返回值类型，避免类型错误。

```python
def _setup_prototypes(self):
    # create_sensor_handle 签名：int create_sensor_handle(void** handle, int mode)
    self._lib.create_sensor_handle.argtypes = [POINTER(c_void_p), ctypes.c_int]
    self._lib.create_sensor_handle.restype = c_int

    # destroy_sensor_handle 签名：int destroy_sensor_handle(void* handle)
    self._lib.destroy_sensor_handle.argtypes = [c_void_p]
    self._lib.destroy_sensor_handle.restype = c_int

    # get_sensor_data 签名：int get_sensor_data(void* handle, DATA_NEED* out)
    self._lib.get_sensor_data.argtypes = [c_void_p, POINTER(DATA_NEED)]
    self._lib.get_sensor_data.restype = c_int
```

## 5. 创建句柄

调用 DLL 中的创建函数，得到底层资源句柄。

```python
def _init_handle(self):
    ret = self._lib.create_sensor_handle(ctypes.byref(self._handle), 5)
    if ret != 0:
        raise RuntimeError(f"Failed to create handle, error code: {ret}")
```

## 6. `__enter__` 方法

支持上下文管理器，进入时返回自身。

```python
def __enter__(self):
    return self
```

## 7. `__exit__` 方法

退出上下文时自动释放资源。

```python
def __exit__(self, exc_type, exc_val, exc_tb):
    self.release()
```

## 8. `__del__` 方法

析构函数，确保对象销毁时释放 DLL 资源。

```python
def __del__(self):
    self.release()
```

## 9. `release` 方法

显式释放句柄，避免资源泄漏。

```python
def release(self):
    if self._handle:
        ret = self._lib.destroy_sensor_handle(self._handle)
        if ret != 0:
            print(f"Warning: Failed to destroy handle, error code: {ret}")
        self._handle = None
```

## 10. `benchmark` 方法

用于性能测试，可测量单次 `get_data` 调用耗时或原始 C 函数调用耗时。

```python
def benchmark(self, iterations=1000, warmup=3, include_data_conversion=False):
    # 预热
    for _ in range(warmup):
        self.get_data()

    timings = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        if include_data_conversion:
            self.get_data()                     # 包含 Python 层转换
        else:
            output = DATA_NEED()
            ret = self._lib.get_sensor_data(self._handle, ctypes.byref(output))
            if ret != 0:
                raise RuntimeError("获取数据失败")
        end_time = time.perf_counter()
        timings.append(end_time - start_time)

    return self._analyze_timings(timings, iterations)
```

## 11. `_analyze_timings` 方法

统计计时数据的均值、中位数、标准差等。

```python
def _analyze_timings(self, timings, iterations):
    avg = statistics.mean(timings)
    median = statistics.median(timings)
    min_t = min(timings)
    max_t = max(timings)
    stdev = statistics.stdev(timings) if iterations > 1 else 0
    return {
        "total_samples": iterations,
        "total_time": sum(timings),
        "average_time": avg,
        "median_time": median,
        "min_time": min_t,
        "max_time": max_t,
        "std_dev": stdev,
        "frequency": 1 / avg,
        "timings": timings if iterations <= 1000 else []
    }
```

## 12. 压测结果打印方法

格式化输出性能测试结果，便于查看。

```python
def print_benchmark_result(self, result):
    print(f"\n性能测试结果（{result['total_samples']}次迭代）:")
    print(f"  - 总耗时: {result['total_time']:.6f} 秒")
    print(f"  - 平均耗时: {result['average_time']*1000:.3f} ms")
    print(f"  - 中位数耗时: {result['median_time']*1000:.3f} ms")
    print(f"  - 最小耗时: {result['min_time']*1000:.3f} ms")
    print(f"  - 最大耗时: {result['max_time']*1000:.3f} ms")
    print(f"  - 标准差: {result['std_dev']*1000:.3f} ms")
    print(f"  - 理论最大频率: {result['frequency']:.2f} Hz")
```

## 13. 静态方法 `is_port_available`

用于检查串口是否可用（存在、可读写且为字符设备）。

```python
@staticmethod
def is_port_available(port="COM5"):
    return all([
        os.path.exists(port),
        os.access(port, os.R_OK),
        os.access(port, os.W_OK),
        stat.S_ISCHR(os.stat(port).st_mode)
    ])
```

## 14. 业务相关方法 `get_data` 与 `get_force`

根据实际业务需求，从 DLL 中获取数据并转换为 Python 可用的格式。

```python
def get_data(self):
    """获取原始数据并转换为 Python 字典"""
    ret = self._lib.get_sensor_data(self._handle, ctypes.byref(self._data_buffer))
    if ret != 0:
        raise RuntimeError(f"Failed to get data, error code: {ret}")
    return self._convert_output(self._data_buffer)

def get_force(self):
    """便捷方法：直接返回第一个力组的 Z 方向合力"""
    data = self.get_data()
    return data['forces'][0]['rest_data'][2]

def _convert_force_3d(self, force):
    """将 RAW_DATA 转为 numpy 数组"""
    return np.array([force.x, force.y, force.z])

def _convert_output(self, output):
    """将 DATA_NEED 结构体转换为 Python 字典"""
    result = {
        'num': output.num,
        'forces': []
    }
    for i in range(output.num):
        data_group = {
            'rest_data': self._convert_force_3d(output.data_group[i].rest_data),
            'component_forces': [],
            'original_forces': []
        }
        comp_datas = []
        orig_forces = []
        for j in range(60):
            comp_datas.append(self._convert_force_3d(output.data_group[i].comp_data[j]))
            orig_f = output.data_group[i].ori_data[j]
            orig_forces.append([orig_f.x, orig_f.y, orig_f.z])
        data_group['component_forces'] = np.array(comp_datas)
        data_group['original_forces'] = np.array(orig_forces, dtype=np.uint8)
        result['forces'].append(data_group)
    return result
```

## 使用示例

```python
if __name__ == "__main__":
    # 创建实例
    handler = SensorHandler()
    
    # 获取一次力数据
    force_z = handler.get_force()
    print(f"Z方向力: {force_z}")
    
    # 运行性能测试
    result = handler.benchmark(iterations=500, warmup=10)
    handler.print_benchmark_result(result)
    
    # 显式释放资源
    handler.release()
```

## 总结

该模板提供了一个安全、可复用的 Python 封装模式，用于加载 C++ 编写的动态库。它包含了资源管理（上下文管理器、析构函数）、类型安全（函数签名）、性能测试和业务数据转换等常见需求，可作为与底层硬件库交互的通用基类。

> **复用的时候除了业务代码都可以直接照搬**，而业务代码也可以作为有效的借鉴。对于 `_setup_prototypes` 中的签名，则需要根据实际的业务动态调整。


## 附录（参考代码）

```python
```python
import ctypes
import os
import stat
import time
import statistics
import numpy as np
from ctypes import Structure, c_float, c_ubyte, c_int, POINTER, c_void_p


# ========================= 0. 定义 C++ 结构体 =========================
class RAW_DATA(Structure):
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("z", c_float)
    ]


class DATA_LAYER_1(Structure):
    _fields_ = [
        ("x", ctypes.c_ubyte),
        ("y", ctypes.c_ubyte),
        ("z", ctypes.c_ubyte)
    ]


class DATA_LAYER_2(Structure):
    _fields_ = [
        ("ori_data", DATA_LAYER_1 * 60),
        ("comp_data", RAW_DATA * 60),
        ("rest_data", RAW_DATA)
    ]


class DATA_NEED(Structure):
    _fields_ = [
        ("data_group", DATA_LAYER_2 * 10),
        ("num", c_int)
    ]


# ========================= 1. 主类封装 =========================
class SensorHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, dll_path: str = "YourDll.dll"):
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self._lib = ctypes.CDLL(dll_path)          # 加载 DLL
        self._setup_prototypes()                  # 设置函数签名
        self._handle = c_void_p()                 # 句柄变量
        self._init_handle()                       # 创建并初始化句柄
        self._data_buffer = DATA_NEED()            # 复用缓冲区

    # --------------------- 3. 签名方法 ---------------------
    def _setup_prototypes(self):
        self._lib.create_sensor_handle.argtypes = [POINTER(c_void_p), ctypes.c_int]
        self._lib.create_sensor_handle.restype = c_int

        self._lib.destroy_sensor_handle.argtypes = [c_void_p]
        self._lib.destroy_sensor_handle.restype = c_int

        self._lib.get_sensor_data.argtypes = [c_void_p, POINTER(DATA_NEED)]
        self._lib.get_sensor_data.restype = c_int

    # --------------------- 4. 创建句柄 ---------------------
    def _init_handle(self):
        ret = self._lib.create_sensor_handle(ctypes.byref(self._handle), 5)
        if ret != 0:
            raise RuntimeError(f"Failed to create handle, error code: {ret}")

    # --------------------- 5. 上下文管理器 ---------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    # --------------------- 6. 析构与释放 ---------------------
    def __del__(self):
        self.release()

    def release(self):
        if self._handle:
            ret = self._lib.destroy_sensor_handle(self._handle)
            if ret != 0:
                print(f"Warning: Failed to destroy handle, error code: {ret}")
            self._handle = None

    # --------------------- 7. 性能测试 ---------------------
    def benchmark(self, iterations=1000, warmup=3, include_data_conversion=False):
        # 预热
        for _ in range(warmup):
            self.get_data()

        timings = []
        for _ in range(iterations):
            start_time = time.perf_counter()
            if include_data_conversion:
                self.get_data()          # 包含 Python 层转换
            else:
                output = DATA_NEED()
                ret = self._lib.get_sensor_data(self._handle, ctypes.byref(output))
                if ret != 0:
                    raise RuntimeError("Failed to get data")
            end_time = time.perf_counter()
            timings.append(end_time - start_time)

        return self._analyze_timings(timings, iterations)

    def _analyze_timings(self, timings, iterations):
        avg = statistics.mean(timings)
        median = statistics.median(timings)
        min_t = min(timings)
        max_t = max(timings)
        stdev = statistics.stdev(timings) if iterations > 1 else 0.0
        return {
            "total_samples": iterations,
            "total_time": sum(timings),
            "average_time": avg,
            "median_time": median,
            "min_time": min_t,
            "max_time": max_t,
            "std_dev": stdev,
            "frequency": 1 / avg if avg > 0 else 0,
            "timings": timings if iterations <= 1000 else []
        }

    def print_benchmark_result(self, result):
        print(f"\n性能测试结果（{result['total_samples']}次迭代）:")
        print(f"  - 总耗时: {result['total_time']:.6f} 秒")
        print(f"  - 平均耗时: {result['average_time'] * 1000:.3f} ms")
        print(f"  - 中位数耗时: {result['median_time'] * 1000:.3f} ms")
        print(f"  - 最小耗时: {result['min_time'] * 1000:.3f} ms")
        print(f"  - 最大耗时: {result['max_time'] * 1000:.3f} ms")
        print(f"  - 标准差: {result['std_dev'] * 1000:.3f} ms")
        print(f"  - 理论最大频率: {result['frequency']:.2f} Hz")

    # --------------------- 8. 静态工具方法 ---------------------
    @staticmethod
    def is_port_available(port="COM5"):
        try:
            return all([
                os.path.exists(port),
                os.access(port, os.R_OK),
                os.access(port, os.W_OK),
                stat.S_ISCHR(os.stat(port).st_mode)
            ])
        except Exception:
            return False

    # --------------------- 9. 业务方法 ---------------------
    def get_data(self):
        """获取原始数据并转换为 Python 字典"""
        ret = self._lib.get_sensor_data(self._handle, ctypes.byref(self._data_buffer))
        if ret != 0:
            raise RuntimeError(f"Failed to get data, error code: {ret}")
        return self._convert_output(self._data_buffer)

    def get_force(self):
        """便捷方法：直接返回第一个力组的 Z 方向合力"""
        data = self.get_data()
        return data['forces'][0]['rest_data'][2]

    @staticmethod
    def _convert_force_3d(force):
        """将 RAW_DATA 转为 numpy 数组"""
        return np.array([force.x, force.y, force.z])

    def _convert_output(self, output):
        """将 DATA_NEED 结构体转换为 Python 字典"""
        result = {
            'num': output.num,
            'forces': []
        }
        for i in range(output.num):
            group = output.data_group[i]
            data_group = {
                'rest_data': self._convert_force_3d(group.rest_data),
                'component_forces': [],
                'original_forces': []
            }
            comp_list = []
            orig_list = []
            for j in range(60):
                comp_list.append(self._convert_force_3d(group.comp_data[j]))
                orig_f = group.ori_data[j]
                orig_list.append([orig_f.x, orig_f.y, orig_f.z])
            data_group['component_forces'] = np.array(comp_list)
            data_group['original_forces'] = np.array(orig_list, dtype=np.uint8)
            result['forces'].append(data_group)
        return result


# ========================= 使用示例 =========================
if __name__ == "__main__":
    # 注意：实际使用时需要将 dll_path 替换为真实路径
    handler = SensorHandler(dll_path="YourDll.dll")
    try:
        force_z = handler.get_force()
        print(f"Z方向力: {force_z}")

        bench_result = handler.benchmark(iterations=500, warmup=10, include_data_conversion=True)
        handler.print_benchmark_result(bench_result)
    finally:
        handler.release()
```
```