# 几何 API 详细映射

## MoveWindow

```cpp
// 子控件：删除，交给布局
m_edit.MoveWindow(10, 10, 200, 30, TRUE);   // MFC
// Qt：.ui 中把 edit 放进布局，代码里不设置几何

// 顶层窗口：合理保留
w->setGeometry(x, y, w, h);   // 一次性设置位置+尺寸
w->setFixedSize(400, 300);    // 固定尺寸、不可拉伸
w->resize(800, 600);          // 仅尺寸
w->move(100, 80);             // 仅位置
```

`bRepaint=TRUE` 在 Qt 中无需对应处理，重绘由事件循环自动调度。

## GetWindowRect / GetClientRect / 屏幕坐标

```cpp
CRect rc; w->GetWindowRect(&rc);       // 屏幕坐标，含边框和标题栏
w->GetClientRect(&rc);                 // 客户区，左上角为 (0,0)

// Qt
QRect frame = w->frameGeometry();       // 屏幕坐标，含窗口装饰（对应 GetWindowRect）
QRect geom  = w->geometry();            // 相对父窗口，不含装饰
QRect client = w->rect();               // 自身坐标系客户区（0,0 起）
QRect inner  = w->contentsRect();       // 减去 layout margins 的区域
```

关键区别：

- `frameGeometry()` 是屏幕坐标且含装饰；`geometry()` 相对父窗口且不含装饰。
- 对子控件，"含边框"的概念由 QFrame/QSS 决定，通常直接用 `rect()` / `geometry()`。
- 需要屏幕坐标下的客户区：`w->mapToGlobal(QPoint(0, 0))` 得到客户区原点。

## SetWindowPos

| flags | Qt |
|---|---|
| `SWP_NOSIZE` | `w->move(x, y)` |
| `SWP_NOMOVE` | `w->resize(w, h)` |
| `SWP_NOZORDER` | 不涉及层级的普通设置 |
| `HWND_TOP` + `SWP_NOSIZE|SWP_NOMOVE` | `w->raise()` |
| `HWND_BOTTOM` | `w->lower()` |
| `HWND_TOPMOST` | `setWindowFlags(flags \| Qt::WindowStaysOnTopHint); w->show();` |
| `HWND_NOTOPMOST` | `setWindowFlags(flags & ~Qt::WindowStaysOnTopHint); w->show();` |
| `SWP_SHOWWINDOW` | `w->show()` |
| `SWP_HIDEWINDOW` | `w->hide()` |
| `SWP_NOACTIVATE` | 避免 `activateWindow()`，只 `raise()` |

置顶注意：修改 flags 后部分平台需要重新 `show()`；频繁切换 flag 可能造成窗口闪烁，尽量在构造时就设定。

## BringToTop / Activate

```cpp
w->raise();             // 仅提升到同层顶部
w->activateWindow();    // 请求激活（获得焦点）
```

`activateWindow()` 在某些窗口管理器下是"请求"，不保证立即获得焦点；不要依赖其即时返回值。

## 尺寸约束

| MFC | Qt |
|---|---|
| `WM_GETMINMAXINFO` 限制最小最大尺寸 | `w->setMinimumSize(...)` / `w->setMaximumSize(...)` |
| `MoveWindow` 强制刷新 | 无需；Qt 自动重绘 |
| `GetSystemMetrics(SM_CXSCREEN)` | `QGuiApplication::primaryScreen()->availableGeometry().width()` |
| `AdjustWindowRect` 计算窗口尺寸 | 通常删除；用 `layout()->sizeHint()` + margins |

## 滚动与可视区

| MFC | Qt |
|---|---|
| `GetClientRect` + 手动滚动 | `QScrollArea::viewport()` + `setWidgetResizable(true)` |
| `ScrollWindow` | `QAbstractScrollArea` 的滚动接口，或 model/view 自动滚动 |
| `GetScrollPos` / `SetScrollPos` | `QScrollBar::value()` / `setValue()` |
