# MFC 消息映射宏 → Qt 信号对照

## 命令与按钮

| MFC 宏 | Qt 信号 | 说明 |
|---|---|---|
| `ON_BN_CLICKED(id, fn)` | `QAbstractButton::clicked(bool checked)` | `QPushButton`/`QCheckBox`/`QRadioButton` |
| `ON_BN_DOUBLECLICKED` | 自定义：子类覆写 `mouseDoubleClickEvent`，或 `eventFilter` | QPushButton 无内建 doubleClicked |
| `ON_COMMAND(id, fn)` | `QAction::triggered(bool checked)` | 菜单、工具栏统一用 action |
| `ON_COMMAND_RANGE(id1, id2, fn)` | 遍历多个 QAction 的 `triggered`，lambda 捕获 id | 或 `QButtonGroup::idClicked(int)`（Qt 5.15+/6） |
| `ON_UPDATE_COMMAND_UI(id, fn)` | 状态变化时调用 `QAction::setEnabled/setChecked/setText` | 也可用 `QAction::changed` 观察 |
| `ON_COMMAND_EX` | `triggered` + 槽返回 bool（改为逻辑判断） | 命令是否处理的语义 |

## 编辑框通知

| MFC 宏 | Qt 信号 |
|---|---|
| `ON_EN_CHANGE` | `QLineEdit::textChanged(const QString&)` / `QTextEdit::textChanged()` |
| `ON_EN_UPDATE` | `textChanged` |
| `ON_EN_SETFOCUS` | `QWidget::` 无信号；用 `eventFilter` 监听 `QEvent::FocusIn` |
| `ON_EN_KILLFOCUS` | `QLineEdit::editingFinished()` 或 `eventFilter` 的 `FocusOut` |
| `ON_EN_MAXTEXT` | `textChanged` 中判断长度，或 `QValidator` |
| `ON_EN_HSCROLL` / `ON_EN_VSCROLL` | `QScrollArea`/`QTextEdit` 滚动条 `valueChanged` |

## 组合框 / 列表框通知

| MFC 宏 | Qt 信号 |
|---|---|
| `ON_CBN_SELCHANGE` | `QComboBox::currentIndexChanged(int)`（用 `QOverload<int>::of`） |
| `ON_CBN_EDITCHANGE` | `QComboBox::editTextChanged(const QString&)`（可编辑时） |
| `ON_CBN_CLOSEUP` | 自定义：事件过滤器/`QComboBox` 子类 |
| `ON_CBN_DROPDOWN` | `QComboBox::` 无内建信号；可用 `aboutToShow` 于 view 或子类 |
| `ON_LBN_SELCHANGE` | `QListWidget::currentRowChanged(int)` / `currentItemChanged` |
| `ON_LBN_DBLCLK` | `QListWidget::itemDoubleClicked(QListWidgetItem*)` |

## 控件通用通知 `ON_NOTIFY`

MFC 用 `NMHDR*` + 通知码统一分发；Qt 用控件专属信号，按原 handler 中的分支拆分：

| MFC 通知码 / 控件 | Qt 信号 |
|---|---|
| `NM_CLICK` / `NM_DBLCLK`（ListCtrl） | `QTreeWidget::itemClicked` / `itemDoubleClicked` |
| `LVN_ITEMCHANGED` | `QTreeWidget::itemSelectionChanged` / `currentItemChanged` |
| `LVN_COLUMNCLICK` | `QHeaderView::sectionClicked(int)` |
| `TVN_SELCHANGED`（TreeCtrl） | `QTreeWidget::currentItemChanged` |
| `NM_RETURN` | 由键鼠事件技能处理 |
| `TTN_GETDISPINFO`（ToolTip） | `QWidget::setToolTip` / `eventFilter` 的 `QEvent::ToolTip` |
| `UDN_DELTAPOS`（UpDown） | `QSpinBox::valueChanged(int)` |
| `SB_ENDSCROLL` / `SB_THUMBTRACK`（ScrollBar） | `QScrollBar::valueChanged(int)` / `sliderReleased` |

把 handler 中基于 `NMHDR::code` 的 switch 拆成多个槽；`NMITEMACTIVATE::iItem`/`iSubItem` 等字段转为 signal 参数（`QTreeWidgetItem*`、列号）。

## WM_ 命令/子通知（由控件发出，非 ON_MESSAGE）

| MFC 宏 | Qt 做法 |
|---|---|
| `ON_WM_COMMAND`（原始） | 通常已被上面专用宏覆盖；残留逻辑改为对应控件信号 |
| `ON_CONTROL_REFLECT` | 控件自绘/自管理：把逻辑放进控件子类自身 |
| `ON_PARENT_NOTIFY` | 自定义信号从子 widget 发到父 widget |

## 参数转换原则

- `CWnd* pWnd` / `HWND` → 删除；用 `sender()`（必要时 `qobject_cast`）或直接用 `ui->` 指针。
- `NMHDR*` → 拆解为具体信号参数（item、column、checked 等）。
- `UINT nID` → 命令 ID 用 lambda 捕获或 `QAction::data()` 保存。
- `BOOL bHandled`（`ON_COMMAND_EX`）→ 业务返回 bool，不再依赖消息分发链。
- `LRESULT` 返回值 → 槽函数通常 `void`；确需返回值时用 `QMetaObject::invokeMethod` 配合 `Q_RETURN_ARG`，或改为直接函数调用。
