# 迁移工程的多模块组织

## 何时拆分 target

| 场景 | 建议 |
|---|---|
| 单对话框/小工具 | 一个 executable target，扁平结构 |
| 多窗口、公共控件、业务库 | 顶层 + `add_subdirectory`，公共部分为 STATIC 库 |
| 逐步迁移（MFC 与 Qt 并存） | Qt 部分独立 target，与 MFC 工程通过明确边界接口通信 |

## 推荐目录结构

```text
MyMfcPort/
├── CMakeLists.txt                 # 顶层：project、find_package、add_subdirectory
├── cmake/
│   └── QtConfig.cmake             # 可选：Qt 版本/组件的统一配置
├── src/
│   ├── app/
│   │   ├── CMakeLists.txt         # add_executable(main.cpp) + link
│   │   └── main.cpp
│   ├── widgets/
│   │   ├── CMakeLists.txt         # add_library(widgets STATIC ...)
│   │   ├── customspinbox.h/.cpp
│   │   └── forms/customspinbox.ui
│   ├── dialogs/
│   │   ├── CMakeLists.txt
│   │   ├── logindialog.h/.cpp/.ui
│   │   └── settingsdialog.h/.cpp/.ui
│   └── core/
│       ├── CMakeLists.txt         # 纯业务库，不依赖 Qt Widgets
│       └── ...
├── resources/
│   ├── app.qrc
│   ├── icons/
│   └── translations/
│       └── app_zh_CN.ts
└── tests/
    └── CMakeLists.txt             # Qt Test（QTestLib）
```

## 顶层 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.19)
project(MyMfcPort LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# MFC_QT_MAJOR 与组件来自 .mfc-qt/config.json
set(MFC_QT_MAJOR 6)   # 5 或 6
if(MFC_QT_MAJOR EQUAL 6)
    find_package(Qt6 REQUIRED COMPONENTS Widgets Network)
    set(MFC_QT_WIDGETS Qt6::Widgets)
    set(MFC_QT_TEST Qt6::Test)
else()
    find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets Network)
    set(MFC_QT_WIDGETS Qt5::Widgets)
    set(MFC_QT_TEST Qt5::Test)
endif()

add_subdirectory(src/core)
add_subdirectory(src/widgets)
add_subdirectory(src/dialogs)
add_subdirectory(src/app)
```

## 子目录示例（控件库）

```cmake
add_library(widgets STATIC
    customspinbox.h
    customspinbox.cpp
    forms/customspinbox.ui
)

target_include_directories(widgets PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(widgets PUBLIC
    ${MFC_QT_WIDGETS}
)
```

公共库用 `PUBLIC` 暴露 Qt 依赖；使用方链接 `widgets` 即自动获得对应版本的 Widgets 目标。

## 主程序 target

```cmake
add_executable(MyApp
    main.cpp
    ../resources/app.qrc
)

target_link_libraries(MyApp PRIVATE
    widgets
    dialogs
    core
    ${MFC_QT_WIDGETS}
)
```

## AUTOUIC 与子目录

- `.ui` 在子目录中时，只要列入该 target 的源文件，AUTOUIC 会生成 `ui_xxx.h` 到构建目录对应位置。
- C++ 中 `#include "ui_customspinbox.h"` 即可，不需手工添加构建目录到 include（AUTOUIC 会处理）。
- 如果 `.ui` 与 `.cpp` 不在同一目录且包含失败，可在 target 上设置 `AUTOUIC_SEARCH_PATHS`：

```cmake
set_target_properties(widgets PROPERTIES
    AUTOUIC_SEARCH_PATHS "${CMAKE_CURRENT_SOURCE_DIR}/forms"
)
```

## 资源组织

`resources/app.qrc` 示例：

```xml
<RCC>
  <qresource prefix="/icons">
    <file>icons/app.png</file>
    <file alias="open">icons/open.svg</file>
  </qresource>
  <qresource prefix="/i18n">
    <file>translations/app_zh_CN.qm</file>
  </qresource>
</RCC>
```

代码中引用：`QIcon(":/icons/app.png")`。`.ui` 中通过 `<resources><include location="../resources/app.qrc"/></resources>` 让 Designer 能看到资源（路径相对 `.ui` 文件）。

## 逐步迁移并存

- 让 Qt 部分成为独立可执行 target，先用数据文件/本地 IPC 与原 MFC 程序通信，降低耦合。
- 或在 Windows 上用 `QWinWidget`/嵌入式窗口把 Qt widget 挂到 MFC 窗口（需 `qtwinmigrate`），此时 Qt target 仍独立构建，通过接口与 MFC 层交互。
- 无论哪种方式，保持 Qt target 可独立编译验证，不把 MFC 头文件混进 Qt target 的 include 路径。

## 测试 target（可选）

```cmake
enable_testing()

add_executable(tst_login tst_login.cpp ../dialogs/logindialog.h ../dialogs/logindialog.cpp ../dialogs/logindialog.ui)
target_link_libraries(tst_login PRIVATE ${MFC_QT_TEST} ${MFC_QT_WIDGETS})
add_test(NAME tst_login COMMAND tst_login)
```
