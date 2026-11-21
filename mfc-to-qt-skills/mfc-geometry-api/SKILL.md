---
name: mfc-geometry-api
description: This skill should be used when replacing MFC window geometry APIs such as MoveWindow, GetWindowRect, GetClientRect, SetWindowPos, ScreenToClient, ClientToScreen and CenterWindow with Qt QWidget geometry methods, including frameGeometry, rect, mapToGlobal, mapFromGlobal and layout-based sizing. Triggers include MoveWindow, GetWindowRect, SetWindowPos, 坐标换算, 控件尺寸.
agent_created: true
---

# MFC 几何 API → Qt

## Overview

把 MFC 中直接操作窗口/控件尺寸与坐标的 API（`MoveWindow`、`GetWindowRect`、`SetWindowPos`、坐标换算、居中）转换为 Qt 的 QWidget 几何接口。**首要原则：子控件的尺寸位置交给 QLayout；几何 API 主要保留给顶层窗口、弹层和自绘部件。**

## Guardrails

- 对**子控件**的 `MoveWindow`/`SetWindowPos`：删除，交给布局（见 `mfc-layout-onsize`）。这是最常见也最容易出错的一类。
- 对**顶层窗口**的尺寸位置：用 `setGeometry()` / `resize()` / `move()`，这是合理保留场景。
- `GetWindowRect`（屏幕坐标，含边框标题栏）与 `GetClientRect`（客户区）语义不同，Qt 中分别对应不同方法，勿混用。
- 坐标换算必须明确坐标系（父窗口客户区、屏幕、全局）；Qt 提供 `mapTo*`/`mapFrom*`。
- 高 DPI 下不要假设 1 px = 1 单位；依赖 Qt 的逻辑坐标与布局。
- 设置 `WindowStaysOnTopHint` 等 flag 后需重新 `show()` 才生效（部分平台）。

## Quick Mapping

| MFC | Qt | 说明 |
|---|---|---|
| `MoveWindow(w, x,y,cx,cy, TRUE)` 子控件 | 删除，用 QLayout | 见布局技能 |
| `MoveWindow(w, ...)` 顶层 | `w->setGeometry(x,y,cx,cy)` 或 `resize`+`move` | |
| `SetWindowPos(..., SWP_NOSIZE)` | `w->move(x,y)` | |
| `SetWindowPos(..., SWP_NOMOVE)` | `w->resize(cx,cy)` | |
| `SetWindowPos(h, HWND_TOPMOST, ...)` | `w->setWindowFlags(w->windowFlags() \| Qt::WindowStaysOnTopHint); w->show();` | 置顶 |
| `SetWindowPos(h, HWND_BOTTOM, ...)` | `w->lower()` | |
| `BringWindowToTop` / `SetForegroundWindow` | `w->raise(); w->activateWindow();` | |
| `GetWindowRect(&rc)` | `w->frameGeometry()`（含边框） | 顶层；`geometry()` 不含边框 |
| `GetClientRect(&rc)` | `w->rect()`；含内容边距用 `contentsRect()` | |
| `rc.Width()` / `rc.Height()` | `rect.width()` / `rect.height()` | |
| `ScreenToClient(pt)` | `w->mapFromGlobal(pt)` | |
| `ClientToScreen(pt)` | `w->mapToGlobal(pt)` | |
| 父窗口内坐标换算 | `child->mapTo(parent, pt)` / `parent->mapFrom(child, pt)` | |
| `CenterWindow()` | 见下例 | 相对父窗口或屏幕 |
| `GetSystemMetrics(SM_CXSCREEN)` | `QGuiApplication::primaryScreen()->availableGeometry()` | |
| `GetSystemMetrics(SM_CXBORDER)` 等 | 通常删除，交给平台/布局 | |
| `SetWindowPos(..., SWP_HIDEWINDOW)` | `w->hide()` | |
| `SetWindowPos(..., SWP_SHOWWINDOW)` | `w->show()` | |
| `SetWindowPos(..., SWP_NOACTIVATE)` | `w->raise()` 而不 `activateWindow()` | |

Detailed notes in `references/geometry-mapping.md` and `references/coordinate-systems.md`.

## CenterWindow Example

```cpp
// 居中到父窗口（推荐）
void centerOnParent(QWidget *w) {
    if (!w->parentWidget()) { centerOnScreen(w); return; }
    QRect pr = w->parentWidget()->geometry();
    w->move(pr.center() - QRect(QPoint(0, 0), w->size()).center());
}

// 居中到屏幕可用区（多屏安全）
void centerOnScreen(QWidget *w) {
    QScreen *screen = w->screen() ? w->screen() : QGuiApplication::primaryScreen();
    const QRect ag = screen->availableGeometry();
    w->move(ag.center() - QRect(QPoint(0, 0), w->size()).center());
}
```

多屏环境用 `w->screen()` 而非总是 `primaryScreen()`；否则窗口可能出现在错误屏幕。

## Common Mistakes

- 把 `GetWindowRect` 直接换成 `geometry()`，忽略边框/标题栏差异，导致定位偏移。
- 用 `mapToGlobal` 换算父窗口内坐标（应使用 `mapTo(parent, pt)`）。
- 改 flag 后不重新 `show()`，置顶/无边框不生效。
- 在子控件上仍调用 `setGeometry()`，与布局冲突导致跳动。
- 用 `QCursor::pos()` 之外的全局坐标未转成本地坐标就 `move()`。
- 硬编码屏幕分辨率，多屏/高 DPI 下错位。

## Bundled References

- `references/geometry-mapping.md`：每个 API 的详细语义与替换代码。
- `references/coordinate-systems.md`：Qt 坐标系与换算规则。

## Output Shape

1. 几何调用清单（API、目标窗口、坐标系、语义）
2. 每个调用的替换方案（布局 / 顶层几何 / 坐标换算）
3. 修改后的代码
4. 居中、置顶、多屏等特殊情况处理
5. 验证（不同屏幕/DPI/窗口状态下位置正确）

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。QWidget 的 `geometry()` / `setGeometry()` / `mapToGlobal()` 等在 Qt 5 / Qt 6 一致。
- 屏幕几何不要用 `QDesktopWidget`（Qt 6 已移除）：Qt 6 用 `QGuiApplication::screenGeometry(widget)` / `screenAt()`；Qt 5.14+ 亦可用 `QGuiApplication`，旧版再回退 `QDesktopWidget`。
- 高 DPI 缩放逻辑按版本处理（Qt 5 需在构造 QApplication 前设置属性，Qt 6 默认开启）。差异总表见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
