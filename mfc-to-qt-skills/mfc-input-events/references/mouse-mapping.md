# 鼠标输入映射

## 事件处理器

| MFC 消息 / handler | Qt |
|---|---|
| `WM_LBUTTONDOWN` / `OnLButtonDown` | `mousePressEvent(QMouseEvent*)`，`e->button()==Qt::LeftButton` |
| `WM_LBUTTONUP` | `mouseReleaseEvent()` |
| `WM_LBUTTONDBLCLK` | `mouseDoubleClickEvent()` |
| `WM_RBUTTONDOWN` / `OnRButtonDown` | `mousePressEvent()` 判断 `Qt::RightButton` |
| `WM_RBUTTONUP` | `mouseReleaseEvent()` 判断 `Qt::RightButton` |
| `WM_MBUTTONDOWN/UP` | 判断 `Qt::MiddleButton` |
| `WM_XBUTTONDOWN` | `Qt::BackButton` / `Qt::ForwardButton` |
| `WM_MOUSEMOVE` / `OnMouseMove` | `mouseMoveEvent()` |
| `WM_MOUSEWHEEL` | `wheelEvent(QWheelEvent*)` |
| `WM_MOUSEHWHEEL` | `wheelEvent()` 的 `angleDelta().x()` |
| `WM_MOUSELEAVE` | `leaveEvent()`；hover 跟踪用 `WA_Hover` |
| `WM_SETCURSOR` | `setCursor(...)` 或在事件中设置 |

## 鼠标按键状态

```cpp
void Widget::mouseMoveEvent(QMouseEvent *e) {
    // buttons() 表示当前按住的按键集合；button() 仅对 press/release 有意义
    if (e->buttons() & Qt::LeftButton) {
        m_dragging = true;
    }
    const QPointF pos = e->position();   // Qt 6；Qt 5 用 e->pos()/localPos()
    const Qt::KeyboardModifiers mods = e->modifiers();
    QWidget::mouseMoveEvent(e);
}
```

- `button()`：引发本次 press/release 的那个按钮。
- `buttons()`：当前所有按住的按钮（位掩码）。
- `position()`：Qt 6 中相对部件的坐标（`QPointF`）；Qt 5 用 `pos()` 或 `localPos()`。
- 需要屏幕坐标：`e->globalPosition()`（Qt 6）/ `e->globalPos()`（Qt 5）。

## 鼠标追踪

MFC 默认收到所有 `WM_MOUSEMOVE`；Qt 默认只在有按键按下时才发送 `mouseMoveEvent`。要接收普通移动：

```cpp
setMouseTracking(true);
// 若需子控件也跟踪，递归设置
for (QWidget *w : findChildren<QWidget *>()) w->setMouseTracking(true);
```

或者用 hover 事件（更轻量）：

```cpp
setAttribute(Qt::WA_Hover);
// 覆写 event() 处理 QEvent::HoverMove / HoverEnter / HoverLeave
```

## 鼠标捕获

MFC `SetCapture()` / `ReleaseCapture()`：Qt 在鼠标 press 后自动把后续鼠标事件投递给接收 press 的 widget，通常无需显式捕获。特殊场景：

```cpp
grabMouse();       // 显式抓取，直到 releaseMouse()
releaseMouse();
QWidget *g = mouseGrabber();   // 查询当前抓取者
```

拖拽 QDrag 时 Qt 会自动处理抓取与释放。

## 滚轮

```cpp
void Widget::wheelEvent(QWheelEvent *e) {
    const QPoint angle = e->angleDelta();   // 通常为 120 的倍数
    const int steps = angle.y() / 120;      // 滚动"格数"
    if (e->modifiers() & Qt::ControlModifier) {
        zoomBy(steps);                       // Ctrl+滚轮缩放
    } else {
        scrollBy(steps * 3);
    }
    e->accept();                             // 或忽略以交给父控件
}
```

- `e->pixelDelta()` 在提供像素级滚动的平台（如触控板）非零，优先使用以获得平滑滚动。
- 不要假设一格等于固定像素；按业务换算。
- 不处理时调用基类或 `e->ignore()`，让父级 `QScrollArea` 处理。

## 右键菜单

```cpp
// 构造时
ui->list->setContextMenuPolicy(Qt::CustomContextMenu);
connect(ui->list, &QWidget::customContextMenuRequested,
        this, &MyDialog::showContextMenu);

void MyDialog::showContextMenu(const QPoint &pos) {
    QMenu menu(this);
    menu.addAction(ui->actionOpen);
    menu.addAction(ui->actionRename);
    menu.addSeparator();
    menu.addAction(ui->actionDelete);
    const QPoint global = ui->list->mapToGlobal(pos);   // 必须转全局
    menu.exec(global);
}
```

`pos` 是相对 `ui->list` 的坐标；`TrackPopupMenu` 中先 `ClientToScreen` 再调用的步骤，对应这里的 `mapToGlobal`。

也可以覆写 `contextMenuEvent(QContextMenuEvent*)`，用 `e->globalPos()`。

## 光标

| MFC | Qt |
|---|---|
| `SetCursor(LoadCursor(NULL, IDC_ARROW))` | `setCursor(Qt::ArrowCursor)` |
| `IDC_HAND` | `Qt::PointingHandCursor` |
| `IDC_WAIT` | `Qt::WaitCursor` / `QApplication::setOverrideCursor` |
| `LoadCursorFromFile` | `QCursor(QPixmap(":/cursors/..."), hotX, hotY)` |
| 悬停变手型 | 按钮/链接类控件通常自动；自绘用 `setCursor` |

## 拖放

MFC `DoDragDrop` + `IDropTarget` → Qt 拖放框架：

```cpp
// 拖拽发起
void Widget::mouseMoveEvent(QMouseEvent *e) {
    if (m_dragging && (e->position() - m_pressPos).manhattanLength() > QApplication::startDragDistance()) {
        auto *drag = new QDrag(this);
        auto *mime = new QMimeData;
        mime->setText(m_selectedText);
        drag->setMimeData(mime);
        drag->exec(Qt::CopyAction | Qt::MoveAction);
    }
}

// 接收方
setAcceptDrops(true);
void Widget::dragEnterEvent(QDragEnterEvent *e) { if (e->mimeData()->hasText()) e->acceptProposedAction(); }
void Widget::dropEvent(QDropEvent *e) { insertText(e->mimeData()->text()); e->acceptProposedAction(); }
```
