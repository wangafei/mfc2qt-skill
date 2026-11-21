# 生命周期事件对照

## 初始化

| MFC | Qt | 说明 |
|---|---|---|
| 构造函数中初始化成员 | 构造函数中 `ui->setupUi(this)` 后 | 先 setupUi 再引用控件 |
| `OnInitDialog()` | 构造函数末尾，或 `showEvent()` + `bool m_initialized` | 需要尺寸/布局已计算时用 showEvent |
| `OnInitDialog` 中 `SetWindowText` | `setWindowTitle(...)` | |
| `OnInitDialog` 中填充列表 | 构造函数或 `showEvent` 中 `addItem` / model 填充 | |
| `OnInitDialog` 中 `CenterWindow()` | 构造函数/`showEvent` 中调用居中（见 geometry 技能） | |
| `OnInitDialog` 返回 FALSE（不设置焦点） | 不调用或调整 `setFocusPolicy` / `setFocus()` | Qt 无返回值语义 |

showEvent 一次性初始化示例：

```cpp
void MyDialog::showEvent(QShowEvent *event) {
    QDialog::showEvent(event);
    if (m_initialized) return;
    m_initialized = true;
    adjustColumnsToViewport();   // 需要实际尺寸的逻辑
}
```

## 关闭与销毁

| MFC | Qt |
|---|---|
| `OnOK()` / `OnCancel()` | `accept()` / `reject()` 或 `QDialogButtonBox` 的 accepted/rejected 信号 |
| `OnClose()` / `WM_CLOSE` | `closeEvent(QCloseEvent*)` |
| 询问是否保存后关闭 | `closeEvent` 中 `QMessageBox::question`，取消则 `event->ignore()` |
| `DestroyWindow()` | `close()` + `WA_DeleteOnClose`，或 `deleteLater()` |
| `PostNcDestroy` 中 `delete this` | `setAttribute(Qt::WA_DeleteOnClose)`；删除由 Qt 管理 |
| `PostMessage(WM_CLOSE)` | `QMetaObject::invokeMethod(w, "close", Qt::QueuedConnection)` |
| 主窗口退出关闭所有非模态 | 父对象所有权自动处理；或遍历 `QApplication::topLevelWidgets()` |

closeEvent 示例（阻止意外关闭）：

```cpp
void EditorDialog::closeEvent(QCloseEvent *event) {
    if (m_dirty) {
        const auto r = QMessageBox::question(
            this, tr("未保存"), tr("是否保存更改？"),
            QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel);
        if (r == QMessageBox::Cancel) { event->ignore(); return; }
        if (r == QMessageBox::Save && !save()) { event->ignore(); return; }
    }
    event->accept();
}
```

## Q_OBJECT 与信号

- 对话框类必须有 `Q_OBJECT` 宏才能使用信号槽。
- 数据回传优先用信号（如 `void userConfirmed(const UserInfo&);`），避免调用方在对话框销毁后读取成员。
- 连接 `QDialogButtonBox`：

```cpp
connect(ui->buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
connect(ui->buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
```

## 析构注意事项

- 析构函数中不要再访问已销毁的子控件；`ui` 指针在 `delete ui` 后置空（如采用指针式 ui）。
- 有时需要在 `closeEvent` 中记录几何/状态（`saveGeometry()`），供下次打开恢复。
- 不要在析构中触发需要事件循环的操作（如 `exec()`）。
- 非模态对话框销毁时通过 `destroyed` 信号通知持有者清空 `QPointer`。
