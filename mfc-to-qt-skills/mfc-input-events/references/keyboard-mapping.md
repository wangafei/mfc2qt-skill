# 键盘输入与快捷键映射

## 键值对照

| MFC 虚拟键 | Qt::Key |
|---|---|
| `VK_RETURN` | `Qt::Key_Return` / `Qt::Key_Enter`（小键盘） |
| `VK_ESCAPE` | `Qt::Key_Escape` |
| `VK_TAB` | `Qt::Key_Tab` / `Qt::Key_Backtab` |
| `VK_BACK` | `Qt::Key_Backspace` |
| `VK_DELETE` | `Qt::Key_Delete` |
| `VK_LEFT/RIGHT/UP/DOWN` | `Qt::Key_Left/Right/Up/Down` |
| `VK_HOME` / `VK_END` | `Qt::Key_Home` / `Qt::Key_End` |
| `VK_PRIOR` / `VK_NEXT` | `Qt::Key_PageUp` / `Qt::Key_PageDown` |
| `VK_SPACE` | `Qt::Key_Space` |
| `VK_CONTROL` | `Qt::Key_Control` |
| `VK_SHIFT` | `Qt::Key_Shift` |
| `VK_MENU` (Alt) | `Qt::Key_Alt` |
| `VK_F1`..`VK_F24` | `Qt::Key_F1`..`Qt::Key_F24` |

## 按键处理模式

```cpp
void MyWidget::keyPressEvent(QKeyEvent *event) {
    // 功能键：用 key() + modifiers()
    if (event->key() == Qt::Key_Delete &&
        event->modifiers() & Qt::ShiftModifier) {
        deleteSelection();
        return;                       // 已处理，不再传播
    }

    // 自动重复：多数"动作"类按键应忽略
    if (event->key() == Qt::Key_Space && !event->isAutoRepeat()) {
        toggle();
        return;
    }

    QWidget::keyPressEvent(event);    // 未处理则交给基类
}
```

`WM_CHAR` 对应文本输入，用 `event->text()` 获取 Unicode 字符串（已处理输入法、修饰键等）：

```cpp
if (!event->text().isEmpty()) {
    insertText(event->text());
}
```

不要为文本输入逐字节解析 `event->key()`；Qt 已处理输入法与键盘布局。

## 修饰键

| MFC | Qt |
|---|---|
| `GetKeyState(VK_SHIFT) & 0x8000` | `event->modifiers() & Qt::ShiftModifier` |
| 任意时刻查询 | `QGuiApplication::keyboardModifiers()` |
| `MK_CONTROL` in mouse message | `mouseEvent->modifiers() & Qt::ControlModifier` |

## 加速键表 → QAction / QShortcut

MFC `ACCELTABLE` 条目如 `"O", ID_FILE_OPEN, VIRTKEY | CONTROL`：

```cpp
auto *openAct = new QAction(tr("&Open..."), this);
openAct->setShortcut(QKeySequence::Open);          // 标准快捷键 Ctrl+O
openAct->setShortcut(QKeySequence("Ctrl+O"));      // 或显式指定
connect(openAct, &QAction::triggered, this, &MainWnd::openFile);
ui->menuFile->addAction(openAct);
ui->toolBar->addAction(openAct);                   // 菜单与工具栏共享 action
```

标准快捷键优先使用 `QKeySequence::StandardKey`（`Open`、`Save`、`Copy`、`Paste`、`Undo` 等），自动适配平台惯例。

不需要菜单项的全局快捷键用 `QShortcut`：

```cpp
auto *sc = new QShortcut(QKeySequence("F5"), this);
connect(sc, &QShortcut::activated, this, &MainWnd::refresh);
```

`QShortcut` 的 context 决定作用范围：`WindowShortcut`（默认）、`ApplicationShortcut`、`WidgetShortcut`。

## PreTranslateMessage 改造

MFC `PreTranslateMessage` 常用于：全局拦截 Enter/Esc、Dialog 内 Tab 导航、快捷键预处理。Qt 对应：

| 场景 | Qt |
|---|---|
| 某个 widget 的所有子控件按键 | `installEventFilter()` 到该 widget，在 filter 中看 `KeyPress` |
| 应用级拦截 | `qApp->installEventFilter(filterObj)` |
| 快捷键 | `QShortcut` / `QAction::setShortcut` |
| Dialog 的 Enter/Esc | `QDialogButtonBox` + 默认按钮；Esc 由 QDialog 默认 `reject()` |
| Tab 导航 | 通常无需处理；用 `setTabOrder()` 与 focus policy |

eventFilter 示例：

```cpp
bool KeyFilter::eventFilter(QObject *watched, QEvent *event) {
    if (event->type() == QEvent::KeyPress) {
        auto *ke = static_cast<QKeyEvent *>(event);
        if (ke->key() == Qt::Key_F2 &&
            qobject_cast<QLineEdit *>(watched)) {
            startEdit(watched);
            return true;               // 消费，不再传递
        }
    }
    return QObject::eventFilter(watched, event);   // 未处理交给基类
}
```

注意返回 `true` 表示"已消费"，事件不再传给目标对象；未处理必须返回基类调用。

## Tab 顺序与焦点

- `.ui` 中控件顺序决定 Tab 顺序；必要时 `setTabOrder(a, b)`。
- `setFocusPolicy(Qt::StrongFocus)` / `NoFocus` 控制是否参与 Tab。
- 对自绘 widget 需要键盘焦点时设置 focus policy 并覆写焦点事件。
