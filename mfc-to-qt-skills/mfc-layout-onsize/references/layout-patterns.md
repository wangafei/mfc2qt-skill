# Qt 布局模式库（OnSize 意图 → 布局树）

脚本 `../scripts/onsize_layout_infer.py` 会输出下面的模式名与布局树。生成 `.ui` 时按本表落地，树中 `H` = `QHBoxLayout`，`V` = `QVBoxLayout`，`G` = `QGridLayout`，叶子是控件。

## 基础模式

### H2 — 左右二等分 / 固定+弹性

MFC：

```cpp
m_edit.MoveWindow(0,   0, cx/2, cy);
m_list.MoveWindow(cx/2, 0, cx/2, cy);
```

布局树：`H(edit[stretch=1], list[stretch=1])`

变体：左固定 200，右侧占满 → `H(tree[fixed 200], table[stretch=1])`；若用户可拖动分隔条 → 外层改 `QSplitter`。

### V2 — 上下分层

MFC：

```cpp
m_toolbar.MoveWindow(0, 0, cx, 40);
m_view.MoveWindow(0, 40, cx, cy - 40);
```

布局树：`V(toolbar[fixed 40], view[stretch=1])`

变体：底部状态栏 `V(view[stretch=1], status[fixed])`。MFC 主框架应改用 `QMainWindow` 内置的 `QToolBar` / `QStatusBar`。

### H3 — 左中右

MFC：

```cpp
m_tree.MoveWindow(0, 0, 200, cy);
m_view.MoveWindow(200, 0, cx - 360, cy);
m_prop.MoveWindow(cx - 160, 0, 160, cy);
```

布局树：`H(tree[fixed 200], view[stretch=1], prop[fixed 160])`

要点：两侧的宽是**纯常量**（不含 `cx`），中间宽度含 `+cx`。stretch 只给中间节点，两侧设 `sizePolicy` 为 Fixed 或设 maximumWidth。

### V_H — 上 + 左中右

MFC：顶部标题/工具栏固定高，下方三段横向：

```cpp
m_header.MoveWindow(0, 0, cx, 60);
m_tree.MoveWindow(0, 60, 180, cy - 60);
m_view.MoveWindow(180, 60, cx - 340, cy - 60);
m_prop.MoveWindow(cx - 160, 60, 160, cy - 60);
```

布局树：`V(header[fixed 60], H(tree[fixed 180], view[stretch=1], prop[fixed 160]))`

### H_V — 左 + 上中下

MFC：左侧导航固定宽，右侧纵向三层：

```cpp
m_nav.MoveWindow(0, 0, 160, cy);
m_top.MoveWindow(160, 0, cx - 160, 80);
m_mid.MoveWindow(160, 80, cx - 160, cy - 200);
m_bottom.MoveWindow(160, cy - 120, cx - 160, 120);
```

布局树：`H(nav[fixed 160], V(top[fixed 80], mid[stretch=1], bottom[fixed 120]))`

### V_H_V — 上 / 左中右 / 下

最典型的主界面：顶部工具栏、左树 + 中表 + 右属性、底部状态栏。

布局树：

```text
V
├─ H(top 内的按钮组 / 标题)      [fixed]
├─ H(tree[fixed], view[stretch=1], prop[fixed])   [stretch=1]
└─ status[fixed]
```

若顶层是 `QMainWindow`，工具栏与状态栏用内置 API，centralWidget 只放中间的 H。

### G — 网格

MFC：多个控件按 `col = cx/N; row = cy/M` 摆放，且横纵边界一致。

布局树：`G(row,col)`，或 `V(H(行1), H(行2), ...)`。列宽/行高若按纯比例计算，用 stretch 表达；若每格固定则用 `setFixedSize`。

### FORM — 表单一列

MFC：标签与输入框成对按行排列，列宽随窗口变化。

布局树：`QFormLayout`，标签列固定、字段列拉伸；删除 OnSize 中所有 `DDX`/标签宽计算。

### FILL — 单控件铺满

MFC：`MoveWindow(0, 0, cx, cy)`。

直接把控件放进根布局并 stretch=1，不需要任何嵌套。

### CORNER — 按钮靠右下

MFC：`MoveWindow(btn, cx - 90, cy - 35, 80, 25)`。

根布局末尾放 `QDialogButtonBox` 或水平 spacer(Expanding) + 垂直 spacer(Expanding)。不要保留坐标计算。

### SPLITTER — 可拖拽分隔

MFC 中存在拖动分隔条后调用 `MoveWindow` 重排两侧，或有 `SetWindowPos(... SWP_...)` 手动处理分隔。

用 `QSplitter` 替代左右/上下容器，设置 `stretchFactor` 与 `setSizes()` 初始值；子控件内部仍用布局。

### STACK — 多页切换

MFC：OnSize 中根据当前页只显示一个子窗口，其余 `ShowWindow(SW_HIDE)`。

用 `QStackedWidget`，根布局 stretch=1；页面切换用 `setCurrentWidget()`，不再手工移动/隐藏重排。

### SCROLL — 内容超出可滚动

MFC：`GetClientRect` 后手动计算滚动条范围。

用 `QScrollArea` + `setWidgetResizable(true)`，内部放一个带布局的 content widget；删除手工滚动条逻辑。

## 组合规则

- 模式可嵌套：脚本输出的树自顶向下读，例如 `V[fixed] → H[stretch] → (fixed, stretch, fixed)` 即 V_H。
- **只有纯常量**尺寸才是"固定"（fixed）；含 `cx`/`cy` 的系数是拉伸/比例：
  - 系数 = 1 → 占满剩余（stretch）
  - 系数 = 1/2、1/3 → 按比例分配（stretch 比例）
  - 系数 = 0 → 固定（fixed）
- MFC 中 `cx - 200` 表示"剩余宽度"，对应中间弹性列；`cx/2` 表示两列等分，对应两个相等的 stretch。
- 间距/边距（如 `+10`、`-20`）在 Qt 中用 layout margin/spacing 表达，不写进 sizePolicy。
- 推断结果只是**建议**：脚本会给出置信度，必须结合控件语义（树、表、属性页、状态栏）人工确认。
