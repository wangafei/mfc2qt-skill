---
name: mfc-to-qt-migration
description: This skill should be used when migrating an MFC (Microsoft Foundation Classes) desktop application to Qt Widgets, including .rc resource to .ui conversion, message maps to signals and slots, DDX/DDV bindings, OnSize layout, MoveWindow/GetWindowRect geometry, modal and modeless dialogs, keyboard/mouse messages, and CMake project setup. Supports configurable Qt 5/Qt 6 targets and persistent user-defined control mappings. Triggers include MFC 迁移 Qt, MFC 转 Qt, rc 转 ui, DoModal, DDX, ON_BN_CLICKED, Qt 版本, 自定义控件映射.
agent_created: true
---

# MFC 到 Qt 迁移总入口

## Overview

作为 MFC → Qt Widgets 迁移的总入口与路由器。先盘点、定策略，再把具体任务分派给专项技能。所有产出统一采用 **Qt Widgets + `.ui` 表单 + 现代 CMake**，不生成 QML 方案。

## Default Assumptions

- C++17；**Qt 版本不预设**：读取项目配置，支持用户指定 Qt 5 / Qt 6 / 具体版本，或自动探测 Qt 5~6。
- UI 固定为 QWidget + QLayout + `.ui`（Qt Designer 表单）+ QSS。
- 构建固定为 CMake，target-based，启用 AUTOMOC / AUTOUIC / AUTORCC；Qt 大版本决定 `find_package` 与链接目标。
- 保留原 MFC 项目的模块边界与业务类；逐窗口/逐对话框迁移，不做一次性重写。
- 业务数据与界面分离：`.ui` 只描述控件结构与 objectName，数据在 C++ 侧。

## Workflow

1. **先定版本与映射配置**：运行 `scripts/migration_config.py`，见 `references/qt-version-config.md`。
   - 用户未指定版本时先 `detect`；探测结果歧义则**询问用户**，不要默认 Qt 6。
   - 用户给出自定义控件对应关系时，用 `map add` 写入配置（默认项目级，可用 `--scope global` 存为个人偏好），随后所有专项技能以用户映射优先。
   - 确认配置落盘后再进入后续步骤；中途改版本要重新检查差异 API 与 CMake。

   ```bash
   python scripts/migration_config.py init --root <mfc-project-root>
   python scripts/migration_config.py detect --root <mfc-project-root>
   python scripts/migration_config.py set-qt auto --root <mfc-project-root>   # 或 5.15 / 6
   python scripts/migration_config.py map add MyGridCtrl QTableView --root <mfc-project-root>
   python scripts/migration_config.py show --root <mfc-project-root>
   ```

2. **盘点**：扫描 MFC 项目，统计 `.rc` 资源、消息映射宏、DDX/DDV、OnSize、几何 API、对话框调用、键鼠处理。运行扫描脚本作为线索：

   ```bash
   python scripts/mfc_scan.py <mfc-project-root>
   python scripts/mfc_scan.py <mfc-project-root> --json
   ```

   扫描结果只作线索，必须结合源码确认。

3. **定策略**：小工具/单对话框整体重写为一个 Qt target；大型程序按窗口逐个迁移，保留 MFC 主框架或通过嵌入式窗口过渡，每个窗口独立编译验证。

4. **按场景路由**（互不依赖的窗口可并行）：

   | 场景 | 技能 |
   |---|---|
   | `.rc` 对话框/菜单/图标 → `.ui` 与 `.qrc` | `mfc-rc-to-ui` |
   | `ON_BN_CLICKED` / `ON_COMMAND` / `ON_NOTIFY` 等消息映射宏 | `mfc-macro-to-slot` |
   | DDX/DDV 与控件成员变量绑定 | `mfc-control-binding` |
   | `OnSize` / `WM_SIZE` 手动重排子控件（自动推断左中右/上下等布局模式） | `mfc-layout-onsize` |
   | `ON_MESSAGE` / 自定义消息 / `SendMessage` / `PostMessage` | `mfc-message-to-slot` |
   | `MoveWindow` / `GetWindowRect` / `SetWindowPos` / 坐标换算 | `mfc-geometry-api` |
   | `DoModal` / `Create` 模态与非模态窗体 | `mfc-dialog-lifecycle` |
   | 键盘 / 鼠标消息与快捷键 | `mfc-input-events` |
   | CMake 工程、`.ui`/`.qrc` 接入、构建错误 | `mfc-to-qt-cmake` |

5. **转换顺序**（每个窗口固定执行，避免返工）：

   ```text
   .rc 资源 → .ui 骨架与 objectName
        → 删除控件类型成员绑定，改 ui-> 访问
        → 消息映射宏改 connect()
        → OnSize/几何代码改 QLayout
        → 模态/非模态生命周期改造
        → 键鼠事件改造
        → CMake 接入并编译验证
   ```

6. **验收**：对照 `references/migration-checklist.md` 逐项确认，再运行现有测试或手工验证窗口行为。

## Global Rules

- 迁移后的 Qt 代码不保留 `afxwin.h`、`CWnd`、`HWND` 依赖，除平台隔离层外不使用 Win32 API。
- 所有 MFC 控件 ID（`IDC_*`）在 `.ui` 中落实为稳定 `objectName`，用动态属性 `mfcId` 保留原 ID 便于追溯。
- 子控件几何一律由 QLayout 管理；`setGeometry()` 仅用于顶层窗口或自绘部件。
- 所有 `connect()` 使用 Qt5/Qt6 函数指针新语法；禁止字符串式 `SIGNAL()/SLOT()`。
- 版本差异 API 必须按 `references/qt-version-compat.md` 处理；不得假设某一个大版本。
- 用户自定义控件映射优先于内置默认表，变更后立即写回配置并存盘。
- QWidget 只能在 GUI 主线程访问；跨线程用信号槽或 `QMetaObject::invokeMethod`。
- 不把 `moc_*.cpp`、`ui_*.h`、`qrc_*.cpp` 加入版本库，由构建工具生成。
- 一次提交只迁移一个可独立验证的窗口，保留原 MFC 分支可回退。

## Bundled Resources

- `references/mfc-qt-mapping.md`：MFC 类/宏/API → Qt 对照总表，先查此表。
- `references/qt-version-config.md`：版本配置的位置、优先级与决策流程。
- `references/qt-version-compat.md`：Qt 5 / Qt 6 差异速查，生成代码前必读。
- `references/migration-checklist.md`：逐窗口迁移验收清单。
- `scripts/mfc_scan.py`：MFC 代码模式扫描器，输出 Markdown 或 JSON 线索报告。
- `scripts/migration_config.py`：版本配置与自定义控件映射的读写、探测、导入导出。

所有专项技能与本技能安装在同一级目录；跨技能脚本/参考文件用 `../<skill>/...` 相对路径引用。

## Output Shape

迁移任务按以下顺序输出：

1. 盘点结论（涉及文件、模式数量、风险点）
2. 迁移策略与批次划分
3. 每个窗口的改造要点（含对照表）
4. 生成/修改的文件清单（`.ui`、`.h`、`.cpp`、`.qrc`、`CMakeLists.txt`）
5. 信号槽连接表
6. 验证方式与遗留事项

Prefer Chinese explanations when the user writes in Chinese.
