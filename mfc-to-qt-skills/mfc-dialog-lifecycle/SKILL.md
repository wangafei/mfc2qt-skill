---
name: mfc-dialog-lifecycle
description: This skill should be used when converting MFC modal dialogs (DoModal) and modeless dialogs (Create/ShowWindow/DestroyWindow) to Qt QDialog exec() and open()/show() with correct ownership, WA_DeleteOnClose, accept/reject results and OnInitDialog initialization. Triggers include DoModal, 模态对话框, 非模态, EndDialog, OnInitDialog, Create dialog.
agent_created: true
---

# MFC 模态/非模态窗体 → Qt

## Overview

把 MFC 对话框的显示方式与生命周期管理转换为 Qt：模态 `DoModal()` → `QDialog::exec()`；非模态 `Create()`/`ShowWindow()` → `new QDialog` + `show()`（`open()` 为窗口模态）。重点是**所有权、销毁时机与返回值语义**一致。

## Guardrails

- 模态对话框用局部栈对象或明确作用域的 `QDialog` 调用 `exec()`；不要在 `exec()` 返回后使用已销毁对象。
- 非模态对话框必须有明确所有权：作为成员/父对象子对象，或设置 `Qt::WA_DeleteOnClose`。二选一，避免重复 delete。
- 禁止 `delete this`（MFC `PostNcDestroy` 常见写法）；用 `WA_DeleteOnClose` + `deleteLater()` 语义。
- `accept()` / `reject()` 代替 `EndDialog(IDOK/IDCANCEL)`；不要手工 `close()` 后再读控件值（控件可能已销毁）。
- `OnInitDialog()` 中一次性初始化移到构造函数 `setupUi()` 之后；需要尺寸已知时移到 `showEvent()` 并加一次性标志。
- 通过 `result()` 获取模态结果；非模态用信号把数据传回，不依赖返回值。

## Decision Guide

| MFC 用法 | Qt 方案 |
|---|---|
| `CMyDlg dlg; if (dlg.DoModal()==IDOK) {...}` | `MyDialog dlg(this); if (dlg.exec()==QDialog::Accepted) {...}` |
| 模态需带参构造 | 构造函数传参，`exec()` 后用 getter 或信号取结果 |
| `dlg.Create(IDD_X, this); dlg.ShowWindow(SW_SHOW);` 成员保存 | 成员 `QDialog*`：`dlg = new MyDialog(this); dlg->show();` 父对象管理生命 |
| 局部 Create 非模态（MFC 常配 delete this） | `auto *dlg = new MyDialog(this); dlg->setAttribute(Qt::WA_DeleteOnClose); dlg->show();` |
| 非模态只需窗口模态 | `dlg->open()`（阻塞父窗口，但不阻塞代码） |
| `EndDialog(IDOK)` | `accept()`；自定义返回码用 `done(code)` |
| `EndDialog(IDCANCEL)` | `reject()` |
| `DestroyWindow()` | `close()`；配合 `WA_DeleteOnClose` 自动销毁，或 `deleteLater()` |
| `OnInitDialog()` | 构造函数 `setupUi()` 后；尺寸相关用 `showEvent()` + 标志位 |
| 主框架弹出对话框 | `this` 作为 parent，保证关闭顺序与任务栏行为 |

## Modal Example

```cpp
// MFC
CLoginDlg dlg;
if (dlg.DoModal() == IDOK) {
    Use(dlg.m_strUser);
}

// Qt
LoginDialog dlg(this);
if (dlg.exec() == QDialog::Accepted) {
    Use(dlg.user());       // 控件仍存活？不：exec 返回后 dlg 仍在作用域内，可读 getter
}
```

更推荐的信号方式（避免依赖对话框对象状态）：

```cpp
connect(&dlg, &LoginDialog::loginRequested, this, &MainWnd::onLogin);
dlg.exec();
```

## Modeless Example

```cpp
// 头文件：QPointer<FindDialog> m_findDlg;

void MainWnd::openFind() {
    if (m_findDlg) {                       // 已存在则激活
        m_findDlg->raise();
        m_findDlg->activateWindow();
        return;
    }
    m_findDlg = new FindDialog(this);      // 父对象所有权
    m_findDlg->setAttribute(Qt::WA_DeleteOnClose);
    connect(m_findDlg, &QObject::destroyed, this, [this]() { m_findDlg = nullptr; });
    connect(m_findDlg, &FindDialog::findRequested, this, &MainWnd::onFind);
    m_findDlg->show();
}
```

用 `QPointer` 在对话框被销毁后自动置空，避免悬空指针；`destroyed` 信号可替代或补充。

## Common Mistakes

- 非模态对话框用栈对象：`void f(){ QDialog d; d.show(); }` → 函数返回即销毁，窗口一闪而过。
- 既设父对象又 `WA_DeleteOnClose` 后又手动 `delete`，双重释放。
- `exec()` 返回后对话框已 `deleteLater()`，仍访问 `ui->` 读数据。
- 用 `close()` 代替 `accept()`，导致 `result()` 不是 Accepted，调用方逻辑错误。
- 在 `showEvent()` 中未加标志位，重复执行原 `OnInitDialog` 逻辑。
- 忘记给对话框设 parent，导致主窗口关闭时对话框残留。

## Bundled References

- `references/modal-modeless.md`：两种模式的代码模板与所有权矩阵。
- `references/lifecycle-events.md`：初始化、关闭、销毁事件对照。

## Output Shape

1. 对话框清单（模态/非模态、创建点、返回处理）
2. 每个对话框的 Qt 方案（exec / open / show + 所有权）
3. 初始化与关闭逻辑迁移
4. 数据回传方式（getter / 信号）
5. 生命周期验证（重复打开、关闭、主窗口退出）

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。`exec()` / `open()` / `show()` / `WA_DeleteOnClose` 在 Qt 5 / Qt 6 语义一致。
- 高 DPI 与屏幕几何相关代码按版本写：Qt 5 需在创建 QApplication 前启用缩放属性，Qt 6 默认开启；居中参考 `QGuiApplication::screenGeometry()`（Qt 5 旧版才用 `QDesktopWidget`）。
- 其余差异见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
