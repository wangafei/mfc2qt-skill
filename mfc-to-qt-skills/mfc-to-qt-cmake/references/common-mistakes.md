# CMake 构建前自检清单

## 配置与查找

- [ ] `cmake_minimum_required` 为 3.19+，Qt 5 与 Qt 6 均满足。
- [ ] 先读取 `.mfc-qt/config.json` 的 `qt.resolvedMajor`；`find_package(Qt5/Qt6 ...)` 与链接目标 `Qt5::Widgets`/`Qt6::Widgets` 与配置一致，不混用。
- [ ] Qt 5 项目使用配置中的 `qt.minVersion`（如 `find_package(Qt5 5.15 REQUIRED ...)`），未凭空写死版本。
- [ ] 需要的模块都列出：用了 QNetwork 就加 `Network`，用了 QSql 就加 `Sql`，否则链接时报未定义符号。
- [ ] Qt 不在默认路径时，配置命令带 `-DCMAKE_PREFIX_PATH=<Qt安装目录>` 或设置 `CMAKE_PREFIX_PATH` 环境变量。
- [ ] 无 qmake 语法残留：`QT +=`、`CONFIG +=`、`RESOURCES +=`、`.pro` 文件。

## 源文件与自动生成

- [ ] `CMAKE_AUTOMOC`/`AUTOUIC`/`AUTORCC` 已启用（全局 `set(... ON)` 或 target 属性）。
- [ ] 每个 `.ui` 文件出现在某个 target 的源文件列表里，否则不会生成 `ui_*.h`。
- [ ] `.qrc` 文件出现在源文件列表里，否则资源不会编译进去。
- [ ] 含 `Q_OBJECT`/`Q_GADGET` 的头文件被 AUTOMOC 扫描到：头文件与同名 `.cpp` 同目录且都在 target 中，或列入 target 源文件。
- [ ] 未把 `ui_*.h`、`moc_*.cpp`、`qrc_*.cpp` 手动加入源文件列表或提交入库。
- [ ] `#include "ui_xxx.h"` 中的 xxx 与 `.ui` 文件名一致（不是 class 名）。

## target 与链接

- [ ] 使用 `add_executable` / `add_library` 的现代 target 写法，不用全局 `include_directories`/`link_libraries`。
- [ ] `target_link_libraries` 指定 `PRIVATE`/`PUBLIC`/`INTERFACE`：公共库头文件暴露 Qt 类型时用 `PUBLIC ${MFC_QT_WIDGETS}`（或对应版本的具体目标）。
- [ ] include 目录用 `target_include_directories(target PRIVATE ...)`。
- [ ] Windows GUI 程序不需控制台窗口：Qt 5 用 `add_executable(app WIN32 ...)`；Qt 6 可用 `qt_add_executable` 或同样使用 `WIN32`。
- [ ] 多 target 时组件依赖通过 target 链接传递，不靠包含路径碰巧可用。

## 资源与翻译

- [ ] `.qrc` 中文件路径相对 `.qrc` 所在目录，且实际存在；`prefix` 与代码中 `:/...` 引用一致。
- [ ] `.ui` 中 `<resources><include location="..."/></resources>` 的路径相对 `.ui` 文件，且该 `.qrc` 已被 target 使用。
- [ ] 翻译文件 `.ts` 由 `lupdate` 生成/更新；如使用 `qt_add_translations`（Qt 6）需相关组件。
- [ ] 图标 `.ico` 在 Windows 下通过 `.rc` 或 target 属性设置应用图标时，该 `.rc` 文件已加入源文件。

## 常见报错速查

| 报错 | 原因 |
|---|---|
| `ui_xxx.h: No such file or directory` | `.ui` 未列入 target 源文件或 AUTOUIC 未开启 |
| 链接时 `undefined reference to vtable for Xxx` | 缺少 `Q_OBJECT`、未运行 moc（头文件未被扫描）、类声明与实现不一致 |
| `Could not find a package configuration file provided by "Qt5"` / `"Qt6"` | `CMAKE_PREFIX_PATH` 未指向 Qt 安装目录，大版本与配置不一致，或组件名拼写错误 |
| 资源 `:/...` 运行时加载失败 | `.qrc` 未加入 target、prefix/路径不匹配 |
| 信号槽运行时报 `No such signal` | 使用了字符串式 `SIGNAL()/SLOT()`，或签名不匹配；改用函数指针新语法 |
| 迁移后出现控制台窗口 | target 未使用 GUI 子系统（检查 WIN32 与所用 Qt 版本的默认行为） |
| 插件无法加载（platform plugin） | 部署时缺少 `platforms/qwindows.dll` 等插件，属部署问题 |

## 验证命令

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH=<Qt路径>
cmake --build build --config Debug
cmake --build build --config Release
```
