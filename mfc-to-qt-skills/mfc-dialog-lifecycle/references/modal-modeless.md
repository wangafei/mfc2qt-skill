# 模态与非模态模式模板

## 所有权矩阵

| 创建方式 | 所有权 | 销毁时机 | 适用 |
|---|---|---|---|
| 栈对象 + `exec()` | 栈 | 离开作用域 | 模态，最简单 |
| `new QDialog(this)` + `exec()` | 父对象 | 父对象销毁 | 模态，需堆分配 |
| 成员 `QDialog*` + `show()` | 父对象 | 父对象销毁或手动 | 非模态，可复用 |
| `new` + `WA_DeleteOnClose` + `show()` | 自行管理 | 关闭时自动 | 非模态，一次性 |
| `new` + `deleteLater()` | 事件循环 | 控制返回事件循环后 | 需要延迟销毁 |

原则：**只选一种所有权机制**。设了父对象仍可用 `WA_DeleteOnClose`（关闭即从父对象移除并销毁），但不要再手动 `delete`。

## 模态模板

```cpp
// 带输入与结果
int MainWnd::askUser() {
    ConfirmDialog dlg(this);
    dlg.setMessage(tr("确认删除？"));
    const int r = dlg.exec();
    return r;   // QDialog::Accepted / Rejected / 自定义 done(code)
}

// 对话框内
void ConfirmDialog::accept() {
    if (!validate()) return;    // 校验失败保持打开
    QDialog::accept();          // 设置 result=Accepted 并关闭
}
```

模态期间 Qt 启动嵌套事件循环，调用方代码阻塞在原处；`exec()` 返回后 `dlg` 仍在作用域内，可安全读取 getter。若对话框自行 `deleteLater()`，则应在 `exec()` 前连接信号取数据，而非返回后读对象。

## 窗口模态 open()

```cpp
void MainWnd::showSettings() {
    if (!m_settingsDlg)
        m_settingsDlg = new SettingsDialog(this);
    m_settingsDlg->open();      // 阻塞与本窗口的交互，但不阻塞代码执行
}
```

`open()` 适合"设置"类窗口：用户必须处理完才能回到父窗口，但调用方不需等待返回值。

## 非模态模板（可复用成员）

```cpp
// 头文件
QPointer<FindDialog> m_findDlg;

void MainWnd::openFind() {
    if (!m_findDlg) {
        m_findDlg = new FindDialog(this);
        connect(m_findDlg, &FindDialog::destroyed, this, [this] { m_findDlg = nullptr; });
    }
    m_findDlg->show();
    m_findDlg->raise();
    m_findDlg->activateWindow();
}
```

父对象销毁时 `m_findDlg` 自动失效，`QPointer` 自动置空。

## 非模态模板（一次性）

```cpp
void MainWnd::showDetails(const Item &item) {
    auto *dlg = new DetailDialog(this);
    dlg->setAttribute(Qt::WA_DeleteOnClose);
    dlg->setItem(item);
    connect(dlg, &DetailDialog::itemChanged, this, &MainWnd::onItemChanged);
    dlg->show();
}
```

关闭即销毁；数据通过信号回传，保存后再关闭。

## 返回码与结果

| MFC | Qt |
|---|---|
| `EndDialog(IDOK)` | `accept()` / `done(QDialog::Accepted)` |
| `EndDialog(IDCANCEL)` | `reject()` / `done(QDialog::Rejected)` |
| `EndDialog(custom)` | `done(custom)`；用 `result()` 读取 |
| `DoModal()` 返回 `IDOK/IDCANCEL` | `exec()` 返回 `QDialog::Accepted/Rejected` |
| 对话框关闭但不想表示接受 | `reject()` 或在 `closeEvent` 中 `event->ignore()` |

## 常见行为对齐

| 行为 | MFC | Qt |
|---|---|---|
| 按 Esc 关闭 | `IDCANCEL` | `reject()`（QDialog 默认处理 Esc） |
| 按 Enter 触发默认按钮 | `BS_DEFPUSHBUTTON` | `QPushButton::setDefault(true)` + `autoDefault` |
| 关闭按钮 (X) | `WM_CLOSE` | `closeEvent()`；默认触发 `reject()` |
| 模态期间禁用父窗口 | 系统自动 | `exec()` / `open()` 自动设置模态 |
| 非模态重复打开 | 需自己判重 | 用 `QPointer` 判重后 `raise()` 已有窗口 |
