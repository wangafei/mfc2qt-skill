# 逐窗口迁移验收清单

每迁移完一个 MFC 窗口/对话框，逐项确认。未通过项计入遗留事项，不要静默跳过。

## 1. 资源与界面

- [ ] `.rc` 中的 `DIALOG`/`DIALOGEX` 已生成对应 `.ui`，objectName 为稳定命名。
- [ ] 每个 `IDC_*` 都有对应 objectName，并保留动态属性 `mfcId`。
- [ ] 菜单、工具栏、快捷键、字符串表、图标已迁入 `.ui` / `.qrc` / `tr()`。
- [ ] 所有控件已放入 QLayout，无绝对坐标死锁；缩放到最小/最大窗口无重叠与截断。
- [ ] 高 DPI 下文字与图标清晰，无硬编码像素依赖。
- [ ] QSS 选择器使用 objectName，无大段内联 `setStyleSheet`。

## 2. 数据与绑定

- [ ] `DoDataExchange()` 已删除；无 `DDX_*` / `DDV_*` 残留。
- [ ] 控件类型成员变量（`CButton m_btn;` 等）已删除，改用 `ui->btn`。
- [ ] 仅保留真正需要的**值类型**成员（如 `QString m_name;`）。
- [ ] `UpdateData(TRUE/FALSE)` 已替换为 `readFromUi()` / `writeToUi()` 或信号同步。
- [ ] 校验规则由 QValidator / QSpinBox 范围 / 提交前校验实现，错误有用户提示。

## 3. 消息与事件

- [ ] `BEGIN_MESSAGE_MAP`/`END_MESSAGE_MAP` 已删除，类声明有 `Q_OBJECT`。
- [ ] 所有消息映射宏改为新语法 `connect()` 或事件处理器覆写。
- [ ] 无字符串式 `SIGNAL()`/`SLOT()`。
- [ ] `ON_MESSAGE`/自定义消息改为信号或 `QEvent`。
- [ ] `SendMessage`/`PostMessage` 改为直接调用/`invokeMethod`/`postEvent`，线程亲和正确。
- [ ] 键盘、鼠标、焦点事件按 Qt 事件处理器实现，`eventFilter` 仅在必要时使用。
- [ ] 信号槽连接表已更新，重复连接使用 `Qt::UniqueConnection` 或确认只连一次。

## 4. 生命周期

- [ ] `DoModal()` 改为 `exec()`，返回值语义保持一致。
- [ ] 非模态窗口有明确所有权，`WA_DeleteOnClose` 或父对象管理；无悬空指针。
- [ ] `OnInitDialog()` 逻辑移到构造函数/`showEvent()`，无重复执行。
- [ ] 关闭/销毁路径不会重复 `delete`，无 `delete this` 残留。
- [ ] 模态期间的输入阻塞与返回后数据读取顺序一致。

## 5. 构建与工程

- [ ] `.mfc-qt/config.json` 已落盘：Qt 版本由用户指定或探测确认，`resolvedMajor` 与生成代码一致。
- [ ] 用户提供的自定义控件映射已写入配置，且 `.ui` / C++ 使用的 widget 与映射一致。
- [ ] `CMakeLists.txt` 用 target-based 写法，`find_package(Qt5/Qt6 REQUIRED COMPONENTS Widgets)` 与配置的 `resolvedMajor` 一致。
- [ ] 版本相关 API（鼠标位置、`nativeEvent`、validator、`QVariant` 等）按 `qt-version-compat.md` 处理。
- [ ] `.ui` 列入 target 源文件，`AUTOUIC` 生效；`.qrc` 列入源文件，`AUTORCC` 生效。
- [ ] `AUTOMOC` 生效，含 `Q_OBJECT` 的头文件被正确扫描。
- [ ] 无 qmake 残留（`QT +=`、`CONFIG +=`、`.pro`）。
- [ ] 无手工生成的 `ui_*.h` / `moc_*.cpp` 入库。
- [ ] Debug/Release 均可编译，无 MFC 头文件依赖残留。
- [ ] 可执行文件路径与资源前缀与原程序一致，安装/部署规则已更新。

## 6. 行为验证

- [ ] 打开、操作、关闭、重开该窗口均正常，无内存泄漏或崩溃。
- [ ] 快捷键、Tab 顺序、默认按钮、Esc/Enter 行为与原程序一致。
- [ ] 与原 MFC 版本并排截屏对比关键界面。
- [ ] 相关自动化测试通过或补充了 Qt 测试。
