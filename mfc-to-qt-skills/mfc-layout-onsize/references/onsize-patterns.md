# OnSize 算式 → 布局结构对照

## 常见算式

| MFC 代码片段 | 语义 | Qt 布局 |
|---|---|---|
| `w = cx/2 - 20; h = cy - 40;` | 左右等分 | `QHBoxLayout` + 两个 `QVBoxLayout` 各 stretch=1，margin 10 |
| `SetWindowPos(hwnd, x, y, cx-300, cy-50, ...)` | 左侧固定 300，右侧自适应 | `QHBoxLayout`：左 widget `setFixedWidth(300)`，右 stretch=1 |
| `MoveWindow(..., 0, cy-40, cx, 40)` | 底部固定高状态条 | 根 `QVBoxLayout`：主区 stretch=1，底部 widget `setFixedHeight(40)` |
| `MoveWindow(btn, cx-90, cy-35, 80, 25)` | 按钮靠右下 | `QHBoxLayout` + `QSpacerItem(Expanding, ...)`, `QDialogButtonBox` 更合适 |
| 按 `nType == SIZE_MINIMIZED` 特殊处理 | 最小化处理 | 通常无需处理；必要时 `changeEvent` 检查 `QEvent::WindowStateChange` |
| 控件随比例 `cx*0.3` | 比例分配 | stretch=3 与 stretch=7 |
| `GetClientRect` + 手动滚动条范围 | 滚动区域 | `QScrollArea` + `setWidgetResizable(true)` |
| 多个子窗口平铺 | MDI/多文档 | `QMdiArea` 或 `QStackedWidget` |

## 复合界面拆解示例

MFC 典型主界面 OnSize：左树固定宽、右表格占满、底部状态栏固定高、顶部工具栏固定高。

```text
QMainWindow
 └─ centralWidget: QVBoxLayout
     ├─ toolBar / QToolBar         (Qt 用 QMainWindow 内置，不进 central layout)
     ├─ QHBoxLayout     stretch=1
     │   ├─ treeWidget  fixed width 240 / QSplitter 左
     │   └─ QTableView  stretch=1 / QSplitter 右
     └─ QStatusBar                 (QMainWindow 内置)
```

对应做法：

- 用 `QMainWindow` 的 `setCentralWidget()` / `addToolBar()` / `statusBar()`，不要手工模仿工具栏与状态栏。
- 左右区域用 `QSplitter`（若用户可拖拽）或 `QHBoxLayout`（若固定比例）。
- 把原 OnSize 中的 `cx/cy` 算式完全删除。

## 表单类对话框

MFC 对话框常把标签和输入框按行排列并在 OnSize 中调整列宽：

```text
QFormLayout
 ├─ labelUser    → editUser
 ├─ labelPass    → editPass
 └─ labelType    → comboType
```

`QFormLayout` 自动对齐标签列；窗口变宽时字段区随之拉伸。不要在 OnSize 中调整标签宽度。

## 极少数需要手写尺寸的情况

| 场景 | 做法 |
|---|---|
| 自定义绘制的图表/画布 | 继承 QWidget，在 `resizeEvent` 更新内部缓存尺寸，调用 `update()` |
| 保持宽高比的子窗口 | 覆写 `heightForWidth(int)` 和 `hasHeightForWidth()` |
| 弹出层/浮层绝对定位 | `setGeometry()` 仅用于此类无布局的顶层/浮层 widget |
| 需要精确像素的绘图工具 | 在自绘 widget 内部用自己的坐标系，不重排其他子控件 |

这些情况下，`setGeometry()` 的作用域限于**自绘部件内部**，不应用于已由布局管理的子控件。
