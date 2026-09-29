本文展示在 Linux 中使用 CMake 构建 C++ 文件的最简完整示例，包含**可执行文件和库文件的分离输出**。

## 1. 多文件项目结构
- **build/**：存放临时构建文件（可以随时删除重新构建）
- **bin/**：存放最终的可执行文件（供用户直接使用）
- **lib/**：存放编译好的库文件
- **include/**：存放公共头文件（供其他项目使用）

### 创建项目目录结构
```bash
mkdir -p my_project/{bin,lib,build,include,src}
cd my_project
touch CMakeLists.txt
touch include/hello.h
touch src/{main.cpp,hello.cpp}
```

### 最终项目结构
```
my_project/
├── bin/           # 可执行文件输出目录（构建后自动生成）
├── lib/           # 库文件输出目录（构建后自动生成）
├── build/         # 构建中间文件目录
├── include/       # 公共头文件
│   └── hello.h
├── src/           # 源代码
│   ├── main.cpp
│   └── hello.cpp
└── CMakeLists.txt
```

### include/hello.h
```cpp
#ifndef HELLO_H
#define HELLO_H

void printHello();

#endif
```

### src/hello.cpp
```cpp
#include <iostream>
#include "hello.h"

void printHello() {
    std::cout << "Hello from library function!" << std::endl;
}
```

### src/main.cpp
```cpp
#include <iostream>
#include "hello.h"

int main() {
    printHello();
    std::cout << "Hello from executable!" << std::endl;
    return 0;
}
```

## 2. CMakeLists.txt 配置

```cmake
# 指定最低CMake版本
cmake_minimum_required(VERSION 3.10)

# 定义项目名称
project(MyProject)

# 设置输出目录（关键配置）
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/bin)  # 可执行文件
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/lib)  # 动态库
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/lib)  # 静态库

# 指定头文件目录
include_directories(${PROJECT_SOURCE_DIR}/include)

# 创建库文件（静态库）
add_library(hello STATIC src/hello.cpp)

# 创建可执行文件
add_executable(myapp src/main.cpp)

# 链接库到可执行文件
target_link_libraries(myapp hello)
```

## 3. 构建和运行完整流程

### 步骤1：进入项目目录
```bash
cd my_project
```

### 步骤2：创建并进入构建目录
```bash
mkdir build
cd build
```

### 步骤3：配置项目（生成构建文件）
```bash
cmake ..
```
输出示例：
```
-- The C compiler identification is GNU 9.4.0
-- The CXX compiler identification is GNU 9.4.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to: /home/user/my_project/build
```

### 步骤4：编译项目
```bash
cmake --build .
```
输出示例：
```
Scanning dependencies of target hello
[ 25%] Building CXX object CMakeFiles/hello.dir/src/hello.cpp.o
[ 50%] Linking CXX static library ../../lib/libhello.a
[ 50%] Built target hello
Scanning dependencies of target myapp
[ 75%] Building CXX object CMakeFiles/myapp.dir/src/main.cpp.o
[100%] Linking CXX executable ../../bin/myapp
[100%] Built target myapp
```

### 步骤5：查看生成的文件
```bash
# 查看bin目录（可执行文件）
ls -l ../bin/
```
输出：
```
-rwxr-xr-x 1 user user 16720 Mar 11 10:00 myapp
```

```bash
# 查看lib目录（库文件）
ls -l ../lib/
```
输出：
```
-rw-r--r-- 1 user user 1590 Mar 11 10:00 libhello.a
```

### 步骤6：运行程序
```bash
../bin/myapp
```
输出：
```
Hello from library function!
Hello from executable!
```

### 步骤7：（可选）清理构建文件
```bash
# 删除build目录（保留bin和lib）
cd ..
rm -rf build

# 如果要彻底清理（包括bin和lib）
rm -rf build bin lib
```

## 4. 完整的命令序列（一键复制版）

```bash
# 创建项目结构
mkdir -p my_project/{bin,lib,build,include,src}
cd my_project

# 创建头文件
cat > include/hello.h << 'EOF'
#ifndef HELLO_H
#define HELLO_H
void printHello();
#endif
EOF

# 创建库源文件
cat > src/hello.cpp << 'EOF'
#include <iostream>
#include "hello.h"
void printHello() {
    std::cout << "Hello from library function!" << std::endl;
}
EOF

# 创建主程序文件
cat > src/main.cpp << 'EOF'
#include <iostream>
#include "hello.h"
int main() {
    printHello();
    std::cout << "Hello from executable!" << std::endl;
    return 0;
}
EOF

# 创建CMakeLists.txt
cat > CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.10)
project(MyProject)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/lib)

include_directories(${PROJECT_SOURCE_DIR}/include)

add_library(hello STATIC src/hello.cpp)
add_executable(myapp src/main.cpp)
target_link_libraries(myapp hello)
EOF

# 构建和运行
cd build
cmake ..
cmake --build .
../bin/myapp
```

## 5. 验证构建结果
```bash
# 验证可执行文件
ls -l ../bin/
file ../bin/myapp

# 验证库文件
ls -l ../lib/
file ../lib/libhello.a

# 运行测试
../bin/myapp
```

## 6. 关键点说明

### 输出目录变量说明
| CMake 变量 | 用途 | 对应目录 |
|------------|------|----------|
| `CMAKE_RUNTIME_OUTPUT_DIRECTORY` | 可执行文件（.exe, .dll） | `bin/` |
| `CMAKE_LIBRARY_OUTPUT_DIRECTORY` | 动态库（.so, .dylib, .dll） | `lib/` |
| `CMAKE_ARCHIVE_OUTPUT_DIRECTORY` | 静态库（.a, .lib） | `lib/` |

### 库类型说明
- `STATIC`：静态库（`.a` 文件），编译时链接到可执行文件
- `SHARED`：动态库（`.so` 文件），运行时加载

这样就完成了可执行文件在 `bin/`、库文件在 `lib/` 的 CMake 项目构建完整流程。