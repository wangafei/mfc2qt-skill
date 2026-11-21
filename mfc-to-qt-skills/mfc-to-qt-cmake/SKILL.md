---
name: mfc-to-qt-cmake
description: This skill should be used when creating or updating CMake build files for MFC-to-Qt Widgets migration projects, including Qt5/Qt6 version selection from project config, find_package, AUTOMOC/AUTOUIC/AUTORCC, .ui and .qrc integration, target structure, resources, translations and common build errors. Triggers include CMake Qt Widgets, AUTOUIC, 迁移 CMake, CMakeLists.txt, .ui 编译, Qt 版本.
agent_created: true
---

# MFC → Qt 工程的 CMake 管理

## Overview

为迁移后的 Qt Widgets 工程建立或改造现代 CMake 构建：target-based，`find_package` 引入 Qt，AUTOMOC/AUTOUIC/AUTORCC 处理元对象、`.ui` 表单与资源，`.ui`/`.qrc` 作为 target 源文件。**Qt 大版本不预设**：从 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor` 读取，Qt 5 与 Qt 6 一视同仁。

## Guardrails

- 使用现代 target-based CMake；CMake 3.19+（Qt 5 与 Qt 6 均满足）。
- 生成前先读配置：Qt 6 用 `find_package(Qt6 REQUIRED COMPONENTS Widgets ...)` 与 `Qt6::Widgets`；Qt 5 用 `find_package(Qt5 <最低版本> REQUIRED COMPONENTS Widgets)` 与 `Qt5::Widgets`。配置未确定时必须先询问用户或用总入口技能的 `migration_config.py detect`。
- 推荐用 `MFC_QT_MAJOR` 变量 + `if()` 的双分支模板，使同一份 CMake 可在 Qt5/Qt6 环境切换；见 `assets/CMakeLists.txt`。
- 启用 `CMAKE_AUTOMOC`、`CMAKE_AUTOUIC`、`CMAKE_AUTORCC`（或 target 属性）；`.ui`/`.qrc` 必须列入 target 源文件才会被 AUTOUIC/AUTORCC 处理。
- 不把 `ui_*.h`、`moc_*.cpp`、`qrc_*.cpp` 加入源文件列表或版本库。
- 无 qmake 残留：不出现 `QT +=`、`CONFIG +=`、`.pro` 文件。
- C++17 起步：`set(CMAKE_CXX_STANDARD 17)`、`set(CMAKE_CXX_STANDARD_REQUIRED ON)`。
- include 目录用 target 级 `target_include_directories()`，避免全局 `include_directories()`。

## Workflow

1. 读取 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor` / `qt.minVersion` / `qt.components`；未配置则运行 `../mfc-to-qt-migration/scripts/migration_config.py show --detect --root <项目根>`，仍无法确定就询问用户。Widgets 必需，Network/Sql/Concurrent 等按需。
2. 选择结构：单 target 小工具用扁平结构；多模块迁移用顶层 `CMakeLists.txt` + `add_subdirectory()`。
3. 从 `assets/CMakeLists.txt` 复制骨架，替换项目名与源文件列表。
4. 把每个窗口的 `.h`/`.cpp`/`.ui` 加入对应 target；`.qrc` 加入资源 target 或主 target。
5. 配置构建：`cmake -S . -B build -DCMAKE_PREFIX_PATH=<Qt安装路径>`，再 `cmake --build build`。
6. 按 `references/common-mistakes.md` 做构建前自检；按 `references/project-structure.md` 组织多目录迁移。

## 版本无关骨架（Qt 5 / Qt 6 双分支）

```cmake
cmake_minimum_required(VERSION 3.19)
project(MyMfcPort LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# 必须与 .mfc-qt/config.json 的 qt.resolvedMajor 一致（5 或 6）
set(MFC_QT_MAJOR 6)
if(MFC_QT_MAJOR EQUAL 6)
    find_package(Qt6 REQUIRED COMPONENTS Widgets)
    set(MFC_QT_WIDGETS Qt6::Widgets)
else()
    find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets)
    set(MFC_QT_WIDGETS Qt5::Widgets)
endif()

add_executable(MyApp
    main.cpp
    mainwindow.h mainwindow.cpp mainwindow.ui
    logindialog.h logindialog.cpp logindialog.ui
    resources/app.qrc
)

target_include_directories(MyApp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(MyApp PRIVATE ${MFC_QT_WIDGETS})
```

选定版本后也可以删掉 `if()` 分支，只保留对应版本的 `find_package` 与链接目标；两种方式都可接受，但**不允许 QT 大版本与配置不一致**。更多模块按 `qt.components` 增加，例如 Qt 6 加 `Sql` 则 `find_package(Qt6 REQUIRED COMPONENTS Widgets Sql)` 并链接 `Qt6::Sql`。

## 多目录结构

```text
CMakeLists.txt            # 顶层：find_package + add_subdirectory
src/
  app/CMakeLists.txt      # 主 executable
  widgets/CMakeLists.txt  # 公共控件库（STATIC）
  resources.qrc
forms/login.ui
```

各子目录自己的 target 显式链接需要的 Qt 组件，公共库用 `target_link_libraries(foo PUBLIC ${MFC_QT_WIDGETS})` 暴露依赖。详见 `references/project-structure.md`。

## Bundled Resources

- `assets/CMakeLists.txt`：Qt 5 / Qt 6 双分支工程骨架，复制后按配置设置 `MFC_QT_MAJOR`。
- `references/common-mistakes.md`：构建前自检清单。
- `references/project-structure.md`：多模块/子目录/资源与翻译组织。

## Output Shape

1. Qt 版本与组件确认
2. 目录结构与 target 划分
3. `CMakeLists.txt` 完整内容（或差异）
4. `.ui`/`.qrc` 接入说明
5. 配置与构建命令（含 `CMAKE_PREFIX_PATH` 提示）
6. 常见错误自检结果

Prefer Chinese explanations when the user writes in Chinese.
