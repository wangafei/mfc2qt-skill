# Qt 坐标系与换算

## 四种常用坐标

| 坐标 | 获取 | 说明 |
|---|---|---|
| 部件自身坐标 | `QPoint(0,0)`、`rect()` | 以部件客户区左上角为原点 |
| 父窗口坐标 | `w->geometry()`、`mapTo(parent, pt)` | 相对直接父部件 |
| 屏幕/全局坐标 | `mapToGlobal(pt)`、`frameGeometry()`、`QCursor::pos()` | 相对虚拟桌面（多屏时为全局） |
| 内容区坐标 | `contentsRect()`、`mapTo(w, ...)` 结合 margins | 排除布局 margin |

## 换算方法

```cpp
QPoint global = w->mapToGlobal(QPoint(10, 20));   // 部件内 → 屏幕
QPoint local  = w->mapFromGlobal(QCursor::pos()); // 屏幕 → 部件内

// 在两个相关部件间换算
QPoint inParent = child->mapTo(parent, QPoint(5, 5));
QPoint inChild  = parent->mapFrom(child, inParent);

// 不相关部件：先转全局再转目标
QPoint g = source->mapToGlobal(p);
QPoint q = target->mapFromGlobal(g);
```

## 对照 MFC

| MFC | Qt |
|---|---|
| `ClientToScreen(hwnd, &pt)` | `w->mapToGlobal(pt)` |
| `ScreenToClient(hwnd, &pt)` | `w->mapFromGlobal(pt)` |
| `MapWindowPoints(hwnd1, hwnd2, ...)` | `w1->mapTo(w2, pt)`（需父子关系）；否则经全局中转 |
| `GetWindowRect` 左上角 | `w->frameGeometry().topLeft()` |
| 鼠标消息的 `LPARAM` 客户区坐标 | `QMouseEvent::position()`（部件内坐标） |
| 鼠标屏幕坐标 | `QCursor::pos()` |

## 弹出菜单定位

MFC `TrackPopupMenu` 常用客户区坐标 + `ClientToScreen`。Qt 中：

```cpp
// 右键菜单：customContextMenuRequested 给出的是部件内坐标
connect(ui->list, &QWidget::customContextMenuRequested, this, [this](const QPoint &pos) {
    QMenu menu(this);
    menu.addAction(ui->actionOpen);
    menu.exec(ui->list->mapToGlobal(pos));   // 必须转全局
});
```

忘记 `mapToGlobal` 是常见错误：菜单会出现在屏幕左上角而非鼠标位置。

## 高 DPI 与多屏

- Qt 使用**逻辑坐标**（设备无关像素）；`devicePixelRatio` 由 Qt 处理，通常不需手工换算。
- 多屏虚拟桌面中全局坐标可能为负；不要假设屏幕左上角为 (0,0)。
- 居中/定位到当前屏幕用 `w->screen()->availableGeometry()`，而非总是主屏。
- 跨屏拖动后 `w->screen()` 会变化；需要时响应 `QEvent::ScreenChangeInternal` 或在移动后重新计算。
- 不要用 `QDesktopWidget`（已废弃）；用 `QGuiApplication::screens()` / `QScreen`。

## 调试建议

- 打印 `w->rect()`、`w->geometry()`、`w->frameGeometry()`、`w->mapToGlobal(QPoint(0,0))` 对比。
- 用 `QCursor::pos()` 与 `mapFromGlobal` 验证鼠标坐标换算。
- 在多屏 + 150%/200% 缩放下复测定位逻辑。
