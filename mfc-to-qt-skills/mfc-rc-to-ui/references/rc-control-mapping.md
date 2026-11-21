# .rc 控件与样式 → Qt 映射明细

> 本表是**内置默认表**。实际转换前必须读取 `<项目根>/.mfc-qt/config.json` 的 `controlMap`，用户自定义映射优先于本表；登记与存盘流程见 `custom-control-mapping.md`。

## 按钮类 `BUTTON`

MFC 按钮类型由控件文本后的样式位（数值或宏名）决定。转换时**先解析样式，再选 widget**。

| 样式 | Qt widget | 关键属性 |
|---|---|---|
| `BS_PUSHBUTTON` | `QPushButton` | `text` 取控件标题 |
| `BS_DEFPUSHBUTTON` | `QPushButton` | C++ 中 `setDefault(true)`；`.ui` 中可设 `default` |
| `BS_CHECKBOX` | `QCheckBox` | 手动维护 tristate 时 `tristate=true` |
| `BS_AUTOCHECKBOX` | `QCheckBox` | 自动状态，默认即可 |
| `BS_3STATE` / `BS_AUTO3STATE` | `QCheckBox` | `tristate=true` |
| `BS_RADIOBUTTON` / `BS_AUTORADIOBUTTON` | `QRadioButton` | 用 `QGroupBox` 或 `QButtonGroup` 分组互斥 |
| `BS_GROUPBOX` | `QGroupBox` | `title` 取控件文本，子控件放入其中 |
| `BS_OWNERDRAW` | `QPushButton` + 子类/QSS | 自绘逻辑改为 paintEvent 或样式表 |
| `BS_BITMAP` / `BS_ICON` | `QToolButton` / `QPushButton` | `setIcon(QIcon(":/..."))` |

注意 `WS_GROUP` 决定 MFC 单选分组边界；Qt 中对应 `QGroupBox` 或 `QButtonGroup` 的分组范围，需人工核对。

## 编辑框 `EDITTEXT`

| 样式 | Qt widget | 属性 |
|---|---|---|
| 默认单行 | `QLineEdit` | `text`、`readOnly`、`maxLength` |
| `ES_MULTILINE` | `QTextEdit` | 纯文本用 `setPlainText()`；富文本另作考虑 |
| `ES_PASSWORD` | `QLineEdit` | `echoMode=Password` |
| `ES_READONLY` | `QLineEdit` | `readOnly=true` |
| `ES_NUMBER` | `QLineEdit` + `QIntValidator` | 或在 C++ 设 validator |
| `ES_UPPERCASE` / `ES_LOWERCASE` | `QLineEdit` | C++ 中 `setInputMethodHints` 或 `textChanged` 归一 |
| `ES_AUTOHSCROLL` / `ES_AUTOVSCROLL` | `QLineEdit` / `QTextEdit` | 默认行为通常已覆盖 |
| `ES_WANTRETURN` | `QTextEdit` | 回车换行；否则回车触发默认按钮 |

## 组合框 `COMBOBOX`

| 样式 | Qt |
|---|---|
| `CBS_DROPDOWN` | `QComboBox`（可编辑） |
| `CBS_DROPDOWNLIST` | `QComboBox`（不可编辑） |
| `CBS_SIMPLE` | `QComboBox` + 列表常显，通常用 `QListView` 替代 |
| `CBS_SORT` | 插入后按字母排序；或 model 预排序 |
| `CBS_HASSTRINGS` | `addItem(QString)` |

## 列表与视图

| `.rc` / 控件类 | Qt | 数据量大时 |
|---|---|---|
| `LISTBOX` | `QListWidget` | `QListView` + `QStringListModel` |
| `LBS_EXTENDEDSEL` | `QListWidget` `selectionMode=ExtendedSelection` | 同 |
| `CONTROL "SysListView32"` 报表 | `QTreeWidget`（列）/ `QTableWidget` | `QTableView` + `QAbstractTableModel` |
| `CONTROL "SysListView32"` 图标 | `QListWidget` `viewMode=IconMode` | `QListView` + model |
| `CONTROL "SysTreeView32"` | `QTreeWidget` | `QTreeView` + `QAbstractItemModel` |
| `CONTROL "msctls_progress32"` | `QProgressBar` | |
| `CONTROL "msctls_trackbar32"` | `QSlider` | `orientation` 依 `TBS_HORZ/VERT` |
| `CONTROL "SysDateTimePick32"` | `QDateTimeEdit` / `QDateEdit` | |
| `CONTROL "msctls_updown32"` | `QSpinBox` 的上下按钮 | 通常合并进 `QSpinBox` |
| `SCROLLBAR` | `QScrollBar` / `QSlider` | |
| `STATIC` + `SS_ICON`/`SS_BITMAP` | `QLabel` + `setPixmap` | |
| `STATIC` + `SS_ETCHEDHORZ`/`SS_ETCHEDVERT` | `QFrame` + `HLine`/`VLine` | |
| `STATIC` 普通文本 | `QLabel` | |

## 通用窗口样式

| MFC 样式 | Qt 属性 / 做法 |
|---|---|
| `WS_DISABLED` | `enabled=false` |
| `WS_VISIBLE` | `visible=true`（通常默认） |
| `WS_BORDER` | `QFrame` `frameShape=Box` 或 QSS border |
| `WS_VSCROLL` / `WS_HSCROLL` | 放入 `QScrollArea`，或 `QAbstractScrollArea` 子类 |
| `WS_TABSTOP` | 加入 Tab 顺序；`.ui` 中的控件顺序即 Tab 顺序 |
| `WS_GROUP` | `QButtonGroup` / `QGroupBox` 分组 |
| `DS_MODALFRAME` | C++ 中 `setWindowModality(Qt::ApplicationModal)` |
| `DS_CENTER` | C++ 中手动居中到父窗口/屏幕 |

## 坐标与 DLU

MFC 对话框模板坐标是**对话框单位（DLU）**，基于系统字体平均字符宽高，不是像素。转换原则：

1. 读取 `DIALOGEX ... , x, y, cx, cy` 和控件的 `x, y, width, height`，只用来判断**相对位置与分组**。
2. 推断布局结构：同一行的按钮 → `QHBoxLayout`；表单标签+输入 → `QFormLayout`；分区 → 嵌套 `QVBoxLayout` 或 `QGroupBox`。
3. `cx/cy` 可作为 `QDialog` 的初始 `geometry`/`minimumSize` 参考，但必须支持后续拉伸。
4. 高 DPI 下不要按像素比例缩放控件；依赖布局与 sizePolicy。
