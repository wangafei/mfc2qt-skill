# Qt 5 / Qt 6 差异速查（迁移专用）

本表只列 MFC → Qt Widgets 迁移中真正会碰到的差异。生成代码前先读 `.mfc-qt/config.json` 的 `qt.resolvedMajor`。

## 通用原则

- **优先写两边都能编译的代码**：函数指针 `connect()`、`QObject::tr()`、`QValidator`、`QMenu`/`QAction` 等绝大多数 Widgets API 在 Qt 5.15 与 Qt 6 中一致。
- 只有必须时才用版本分支，并用 `QT_VERSION_CHECK(6, 0, 0)` 包住：

```cpp
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
    const QPointF p = e->position();
#else
    const QPointF p = e->localPos();
#endif
```

- CMake 侧不要写 `if(QT_VERSION ...)` 猜测；直接用配置的 `resolvedMajor` 选择 `find_package(Qt5/Qt6)`。

## 高频差异表

| 场景 | Qt 5.15+ | Qt 6 | 迁移建议 |
|---|---|---|---|
| 函数指针 connect | 支持 | 支持 | 优先用 `QOverload<T>::of()`，两边通用 |
| 重载信号消歧 | `QOverload<int>::of(&QComboBox::currentIndexChanged)` | `qOverload<int>(&QComboBox::currentIndexChanged)` | 统一用 `QOverload`，Qt6 也可编译 |
| 鼠标事件坐标 | `e->pos()` / `e->localPos()` / `e->globalPos()` | `e->position()` / `e->globalPosition()` | 用条件编译包一层 helper |
| 滚轮事件 | `e->angleDelta()` / `e->pixelDelta()` | 同左 | 无差异 |
| 键盘事件 | `e->key()` / `e->modifiers()` / `e->text()` | 同左 | 无差异 |
| 快捷键 | `QShortcut` / `QAction::setShortcut` | 同左 | 无差异 |
| 正则表达式 | `QRegularExpression` | `QRegularExpression` | 不要新写 `QRegExp`（Qt6 已移除） |
| 输入校验 | `QRegularExpressionValidator` | 同左 | 不要新写 `QRegExpValidator` |
| 编码转换 | `QTextCodec::fromUnicode()` | `QStringConverter` / 直接 UTF-8 | 迁移时优先统一 UTF-8 |
| 桌面几何 | `QApplication::desktop()->geometry()` | `QGuiApplication::screenGeometry(w)` | 条件编译；Qt5.14+ 也可用 `QGuiApplication::screenAt()` |
| 样式 margins | `layout->setMargin(0)`（Qt5 弃用） | `layout->setContentsMargins(0,0,0,0)` | 统一用 `setContentsMargins` |
| QVariant 类型 | `v.type()` | `v.metaType()` | 用 `v.userType()` 或按目标版本选 |
| QString 视图 | `QStringRef` | `QStringView` | Qt5.15+ 可用 `QStringView` |
| 信号映射器 | `QSignalMapper`（已弃用） | 移除 | 一律用 lambda 捕获参数 |
| nativeEvent 结果 | `long *result` | `qintptr *result` | 条件编译隔离在平台层 |
| 高 DPI 缩放 | `QT_SCALE_FACTOR` / AA_EnableHighDpiScaling | 默认开启 | 只在 Qt5 设 attribute，且须在 QApplication 之前 |
| Qt Resource | `.qrc` + AUTORCC | 同左 | 无差异 |
| `.ui` 表单 | Qt Designer 4.0 格式 | 同左 | 无差异 |
| 翻译 | `lupdate`/`lrelease` + `Qt5::LinguistTools` | 同左或 `qt_add_translations` | 用传统 lupdate 流程两边通用 |
| 字体 | `QFontDatabase` | 同左 | 无差异 |
| QButtonGroup 点击 | `buttonClicked(int)` | `idClicked(int)` | Qt5.15+ 两者都有；优先 `idClicked` |
| QHeaderView | `setSectionResizeMode`（Qt5 起） | 同左 | 无差异 |

## CMake 差异

| 项目 | Qt 5 | Qt 6 |
|---|---|---|
| 查找包 | `find_package(Qt5 5.15 REQUIRED COMPONENTS Widgets)` | `find_package(Qt6 REQUIRED COMPONENTS Widgets)` |
| 链接目标 | `Qt5::Widgets` | `Qt6::Widgets` |
| 可执行文件 | `add_executable(app WIN32 ...)` | `qt_add_executable(app ...)` 或 `add_executable` |
| 项目初始化 | 无 | 可选 `qt_standard_project_setup()` |
| 翻译 | `Qt5::LinguistTools` + `qt_add_translate_ts` 手写 | 可选 `qt_add_translations` |
| CMake 最低版本 | 3.16+ 即可 | 3.16+，系列统一 3.19 |

完整双分支模板见 `../../mfc-to-qt-cmake/assets/CMakeLists.txt`。

## 各专项技能关注点

- `mfc-rc-to-ui`：控件类型本身基本无差异；只注意 QSS 属性名与 `QRegularExpressionValidator`。
- `mfc-macro-to-slot`：重载信号用 `QOverload`；`QSignalMapper` 改 lambda。
- `mfc-control-binding`：validator 用 `QRegularExpressionValidator`；`QVariant` 类型判断按版本选。
- `mfc-layout-onsize`：`setContentsMargins`；`QSizePolicy` 枚举名一致。
- `mfc-message-to-slot`：`QMetaObject::invokeMethod` 函数指针重载在 Qt5.10+ 可用；`nativeEvent` 签名差异。
- `mfc-geometry-api`：`QGuiApplication::screenGeometry` / `screenAt`；`QDesktopWidget` 仅 Qt5。
- `mfc-dialog-lifecycle`：`open()`/`exec()` 无差异；高 DPI 与父窗口居中 API 有差异。
- `mfc-input-events`：鼠标位置 API、`QKeyEvent` 的 `key()` 一致；原生事件签名差异。
- `mfc-to-qt-cmake`：见上表；生成前必须读配置。
