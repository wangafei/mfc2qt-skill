---
name: mfc-input-events
description: This skill should be used when converting MFC keyboard and mouse message handlers such as WM_KEYDOWN, WM_CHAR, WM_LBUTTONDOWN, WM_MOUSEMOVE, WM_MOUSEWHEEL, PreTranslateMessage, accelerator tables and mouse capture to Qt key/mouse event handlers, event filters, QShortcut/QAction shortcuts and context menus. Triggers include 键盘消息, 鼠标消息, PreTranslateMessage, WM_KEYDOWN, OnMouseMove, 快捷键.
agent_created: true
---

# MFC 键盘/鼠标消息 → Qt 事件

## Overview

把 MFC 的键盘、鼠标消息处理与加速键机制转换为 Qt 的事件处理器、`eventFilter()`、`QShortcut`/`QAction` 快捷键与上下文菜单。范围：输入事件；其他自定义消息见 `mfc-message-to-slot`。

## Guardrails

- 优先用**事件处理器覆写**（`keyPressEvent()`、`mousePressEvent()` 等）处理本 widget 的输入；只在需要监听/拦截**其他对象**的事件时才用 `eventFilter()`。
- 加速键/菜单快捷键用 `QAction::setShortcut()` / `QShortcut`，不要手工在 `PreTranslateMessage` 中比对键码。
- 处理完事件后，若不希望继续传播则不再调用基类；若希望保留默认行为则调用基类实现。
- 键盘事件注意 `event->isAutoRepeat()`、`modifiers()`；鼠标事件注意 `button()` 与 `buttons()` 的区别、`position()` 为部件内坐标。
- 上下文菜单用 `customContextMenuRequested` 或 `contextMenuEvent()`，并 `mapToGlobal()` 定位。
- 不要在输入事件中做耗时操作；耗时任务投递到 worker。

## Quick Mapping

| MFC | Qt |
|---|---|
| `WM_KEYDOWN` / `OnKeyDown` | `keyPressEvent(QKeyEvent*)` |
| `WM_KEYUP` / `OnKeyUp` | `keyReleaseEvent(QKeyEvent*)` |
| `WM_CHAR` / `OnChar` | `keyPressEvent()` 中 `event->text()` |
| `WM_SYSKEYDOWN` (Alt+...) | `keyPressEvent()` + `modifiers()`，或 `QAction` 快捷键 |
| `PreTranslateMessage` 拦截键 | `eventFilter()`（安装到 qApp 或目标 widget），或 `QShortcut` with `WindowShortcut`/`ApplicationShortcut` |
| 加速键表 `ACCELTABLE` | `QAction::setShortcut(QKeySequence(...))` |
| `TranslateAccelerator` | 由 Qt 快捷键系统自动处理 |
| `GetKeyState(VK_SHIFT)` | `QGuiApplication::keyboardModifiers()` 或事件 `modifiers()` |
| `WM_LBUTTONDOWN` / `OnLButtonDown` | `mousePressEvent(QMouseEvent*)` |
| `WM_LBUTTONUP` | `mouseReleaseEvent()` |
| `WM_LBUTTONDBLCLK` | `mouseDoubleClickEvent()` |
| `WM_RBUTTONDOWN` | `mousePressEvent()` 中判断 `Qt::RightButton`，或 `contextMenuEvent()` |
| `WM_MOUSEMOVE` / `OnMouseMove` | `mouseMoveEvent()`（需 `setMouseTracking(true)` 才能接收无按键移动） |
| `WM_MOUSEWHEEL` | `wheelEvent(QWheelEvent*)`，`angleDelta()` |
| `WM_MOUSELEAVE` | `QEvent::Leave` / `leaveEvent()`；hover 用 `WA_Hover` + `QHoverEvent` |
| `SetCapture` / `ReleaseCapture` | 鼠标按下时 Qt 自动抓取；`mouseGrabber()` / `grabMouse()` / `releaseMouse()` |
| `TrackPopupMenu` | `QMenu::exec(mapToGlobal(pos))` |
| `SetCursor` / `LoadCursor` | `setCursor(Qt::...Cursor)` 或 `QCursor(QPixmap(...))` |
| `WM_SETFOCUS` / `WM_KILLFOCUS` | `focusInEvent()` / `focusOutEvent()` |
| `VK_TAB` 导航 | `setTabOrder()` / widget 的 tab 属性；通常不手工处理 |

Detailed in `references/keyboard-mapping.md` and `references/mouse-mapping.md`.

## Example

```cpp
// MFC
void CCanvas::OnLButtonDown(UINT nFlags, CPoint point) {
    m_dragging = true;
    SetCapture();
    m_last = point;
}
void CCanvas::OnMouseMove(UINT nFlags, CPoint point) {
    if (m_dragging) { DrawLine(m_last, point); m_last = point; }
}
void CCanvas::OnLButtonUp(UINT nFlags, CPoint point) {
    m_dragging = false;
    ReleaseCapture();
}

// Qt
void Canvas::mousePressEvent(QMouseEvent *e) {
    if (e->button() == Qt::LeftButton) {
        m_dragging = true;
        m_last = e->position().toPoint();   // Qt 6；Qt 5 用 e->pos()
    }
}
void Canvas::mouseMoveEvent(QMouseEvent *e) {
    if (m_dragging) {
        const QPoint p = e->position().toPoint();
        drawLine(m_last, p);
        m_last = p;
    }
}
void Canvas::mouseReleaseEvent(QMouseEvent *e) {
    if (e->button() == Qt::LeftButton) m_dragging = false;
}
```

Qt 在鼠标按下期间自动把后续鼠标事件送给接收 press 的 widget，一般无需显式 `grabMouse()`。

## Common Mistakes

- 在 `keyPressEvent` 中漏掉 `isAutoRepeat()` 判断，导致长按重复触发动作。
- 用 `event->key()` 与字符混淆：文本输入用 `event->text()`，功能键用 `event->key()`。
- 忘记 `setMouseTracking(true)`，`mouseMoveEvent` 只在按键按下时触发。
- 把滚轮 `angleDelta().y()` 当像素直接用：通常除以 120 得到"格数"，或按业务换算。
- `PreTranslateMessage` 直接搬成 `eventFilter` 却安装到错误对象，收不到事件。
- 上下文菜单没有 `mapToGlobal`，菜单出现在错误位置。
- 覆写事件处理器却不调用基类，破坏默认行为（如 Tab 导航、快捷键）。

## Bundled References

- `references/keyboard-mapping.md`：键盘消息、加速键、PreTranslateMessage 改造。
- `references/mouse-mapping.md`：鼠标消息、捕获、滚轮、右键菜单。

## Output Shape

1. 输入处理清单（消息、目标控件、行为）
2. 每个处理点的 Qt 实现方式（事件处理器 / filter / 快捷键）
3. 修改后的 `.h` / `.cpp` 片段
4. 事件传播与基类调用说明
5. 快捷键表与上下文菜单定义
6. 验证（键盘导航、鼠标拖拽、滚轮、右键菜单）

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。
- 键盘 API（`key()` / `modifiers()` / `text()`）在 Qt 5 / Qt 6 一致。
- 鼠标位置：Qt 6 用 `e->position()` / `e->globalPosition()`；Qt 5 用 `e->pos()` / `e->localPos()` / `e->globalPos()`。用 `QT_VERSION_CHECK(6, 0, 0)` 封装 helper，避免在每个处理器里散落分支。
- 原生事件 `nativeEvent()` 的结果参数 Qt 5 为 `long *`、Qt 6 为 `qintptr *`。差异总表见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
