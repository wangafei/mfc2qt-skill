# Qt 布局 API 要点

## 布局选择

| 布局 | 适用 |
|---|---|
| `QVBoxLayout` / `QHBoxLayout` | 线性排列，最常见 |
| `QGridLayout` | 表格状对齐，跨行跨列 |
| `QFormLayout` | 标签-字段表单，自动对齐与 buddy |
| `QStackedLayout` | 同一区域多页切换（widget 版用 `QStackedWidget`） |
| `QSplitter` | 用户可拖拽调整尺寸的分隔面板 |

## sizePolicy 速查

`QSizePolicy` 由水平/垂直策略组成：

| 策略 | 含义 | 典型控件 |
|---|---|---|
| `Fixed` | 不伸缩 | 固定尺寸按钮、标题条 |
| `Minimum` | 可取 minimumSizeHint，尽量小 | QLabel |
| `Preferred` | 默认，可取 sizeHint，可伸缩 | QPushButton、QComboBox |
| `Expanding` | 尽量占满可用空间 | QTableView、QTextEdit、主内容区 |
| `MinimumExpanding` | 至少 minimumSizeHint 且尽量扩展 | 内容型控件 |
| `Ignored` | 忽略 sizeHint，完全按 stretch | 特殊布局 |

设置方式：`.ui` 的 `sizePolicy` 属性，或 C++ `widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);`。

## stretch factor

- `layout->addWidget(w, stretch)` 或 `addStretch(n)`；stretch 只在空间**分配**时起作用，不是比例缩放控件本身。
- `addStretch(1)` 放在末尾把控件推向一侧；放在中间按比例留白。
- 两个子布局 stretch 均为 1 → 各占一半；3 与 7 → 3:7。
- 设置 stretch 后，控件自身 sizePolicy 应允许伸缩（如 Expanding），否则 stretch 效果不明显。

## margin 与 spacing

- `setContentsMargins(left, top, right, bottom)` 控制布局边距；`setSpacing(n)` 控制控件间距。
- `.ui` 中对每个主要容器显式设置，避免不同平台默认值不一致。
- 用 QSS 的 `padding`/`margin` 与布局 margin 叠加时需注意重复留白。

## QSplitter

```cpp
auto *splitter = new QSplitter(Qt::Horizontal, this);
splitter->addWidget(ui->treeWidget);
splitter->addWidget(ui->tableView);
splitter->setStretchFactor(0, 1);
splitter->setStretchFactor(1, 3);
splitter->setCollapsible(0, false);     // 左栏不可折叠
```

对应 MFC 中可拖拽分隔条 + `OnSize` 计算两栏宽度的逻辑。`.ui` 中可直接放 QSplitter 容器。

## QStackedWidget

对应 MFC 属性页/多视图切换：

```cpp
ui->stackedWidget->setCurrentWidget(ui->pageDetail);
```

用 `currentChanged(int)` 信号驱动左侧导航高亮，替代 MFC `TCN_SELCHANGE` + 手工 ShowWindow/Swap。

## 最小尺寸与高 DPI

- 设置 `setMinimumSize()` 保证窗口缩小时控件不被压缩到不可用；root widget 的 minimumSizeHint 会影响整个对话框最小尺寸。
- 不要按固定像素假设控件尺寸；用 sizeHint + sizePolicy。
- 图标用 SVG 或多分辨率 PNG；QSS 中用逻辑像素。
- 验证：`QT_SCALE_FACTOR=1.5` / `2` 启动程序检查布局。

## 调试技巧

- Qt Designer 中切换不同窗口尺寸预览。
- 临时给布局容器设置醒目 QSS 背景色，观察各区域实际分配。
- `QLayout::setSizeConstraint(QLayout::SetMinimumSize)` 在特殊对话框里控制最小尺寸行为。
