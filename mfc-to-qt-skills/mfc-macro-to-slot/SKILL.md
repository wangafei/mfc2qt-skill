---
name: mfc-macro-to-slot
description: This skill should be used when converting MFC message-map macros such as ON_BN_CLICKED, ON_COMMAND, ON_COMMAND_RANGE, ON_UPDATE_COMMAND_UI, ON_NOTIFY, ON_CBN_SELCHANGE, ON_EN_CHANGE and ON_LBN_SELCHANGE to Qt signals and slots. Triggers include 消息映射宏, ON_BN_CLICKED, BEGIN_MESSAGE_MAP, 宏转信号槽.
agent_created: true
---

# MFC 消息映射宏 → Qt 信号槽

## Overview

把 `BEGIN_MESSAGE_MAP` 中的宏条目转换为 Qt 新语法 `connect()` 或事件处理器覆写。范围限定为**控件通知与命令宏**；`ON_MESSAGE`/自定义消息见 `mfc-message-to-slot`，键鼠消息见 `mfc-input-events`。

## Guardrails

- 删除整个 `BEGIN_MESSAGE_MAP`/`END_MESSAGE_MAP` 宏块；类声明加 `Q_OBJECT`。
- 只用函数指针新语法：`connect(sender, &Sender::signal, this, &Class::slot)`。禁止字符串式 `SIGNAL()/SLOT()`。
- 信号来源优先是 `.ui` 中的控件指针（`ui->btn`）或 `QAction`，不再按 ID 查表分发。
- 槽函数签名与信号参数匹配；参数不匹配时用 lambda 适配，注意 lambda 捕获的生命周期。
- 重复进入 `setupUi()`/重建控件时避免重复连接，必要时用 `Qt::UniqueConnection`。

## Workflow

1. 列出消息映射块中每条宏，查 `references/macro-mapping.md` 确定 Qt 信号与控件 objectName。
2. 在 C++ 包装类构造函数中（`ui->setupUi(this)` 之后）集中建立连接，或按业务分组建立 `connectXxxSignals()` 私有方法。
3. 把原宏对应的处理函数改造为槽函数，保留业务逻辑，去掉 MFC 参数（`NMHDR*`、`CWnd* pWnd` 等）。
4. 处理 `ON_UPDATE_COMMAND_UI`：改为数据变化时更新 `QAction`/控件的 enabled、checked、text。
5. 处理 `ON_COMMAND_RANGE`：遍历 QAction/QButtonGroup，或用 lambda 捕获命令 ID 分发。
6. 更新 `references/connection-table.md`（如项目维护连接表），并逐条验证触发。

## Quick Examples

```cpp
// MFC
BEGIN_MESSAGE_MAP(CLoginDlg, CDialogEx)
    ON_BN_CLICKED(IDC_BTN_OK, &CLoginDlg::OnBnClickedOk)
    ON_EN_CHANGE(IDC_EDIT_USER, &CLoginDlg::OnEnChangeUser)
    ON_CBN_SELCHANGE(IDC_COMBO_TYPE, &CLoginDlg::OnCbnSelchangeType)
END_MESSAGE_MAP()

// Qt
LoginDialog::LoginDialog(QWidget *parent) : QDialog(parent), ui(new Ui::LoginDialog)
{
    ui->setupUi(this);
    connect(ui->btnOk, &QPushButton::clicked, this, &LoginDialog::onOkClicked);
    connect(ui->editUser, &QLineEdit::textChanged, this, &LoginDialog::onUserChanged);
    connect(ui->comboType, QOverload<int>::of(&QComboBox::currentIndexChanged),
            this, &LoginDialog::onTypeChanged);
}
```

重载信号（如 `QComboBox::currentIndexChanged(int)` / `(QString)`、`QSpinBox::valueChanged(int)` / `(double)`）必须用 `QOverload<T>::of()` 或 `qOverload<T>()` 消除歧义；Qt 6 可用 `&QComboBox::currentIndexChanged` 配合 `QOverload`。

## Common Mistakes

- 用 `SIGNAL(clicked())` / `SLOT(onOk())` 字符串连接：编译期不检查，改名后静默失效。
- 忘记 `Q_OBJECT`，导致 `connect` 编译失败或信号不触发。
- 把 `ON_COMMAND` 误挂到按钮而非 `QAction`，导致菜单/工具栏不触发。
- `ON_NOTIFY` 中依赖 `NMHDR` 结构字段，未改为控件专属信号参数。
- lambda 捕获了即将销毁的控件指针，或捕获 `[=]` 造成悬空 `this`。
- `ON_UPDATE_COMMAND_UI` 用定时器轮询，而不是在数据/状态变化时更新。

## Bundled References

- `references/macro-mapping.md`：逐条宏 → Qt 信号对照。
- `references/connection-table.md`：连接表模板与维护约定。

## Output Shape

1. 宏 → 信号槽映射表（原宏、控件、Qt 信号、槽、参数适配）
2. 修改后的类声明与连接代码
3. 槽函数改造要点
4. `ON_UPDATE_COMMAND_UI` / `ON_COMMAND_RANGE` 的处理说明
5. 验证清单

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。函数指针 `connect()` 在 Qt 5 与 Qt 6 都可用。
- 重载信号消歧：Qt 5 用 `QOverload<T>::of(&Class::signal)`；Qt 6 可写 `qOverload<T>(&Class::signal)`。优先用 `QOverload`，两个版本都能编译。
- 不要生成 `QSignalMapper`（Qt 6 已移除），改用 lambda 捕获 id/参数。
- 其他版本差异见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
