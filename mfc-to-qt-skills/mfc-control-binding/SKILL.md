---
name: mfc-control-binding
description: This skill should be used when replacing MFC DDX/DDV data exchange and control-type member variables (CButton, CEdit, CListCtrl members) with Qt Widgets .ui access, using ui pointers, value-type members, QValidator and explicit readFromUi/writeToUi. Triggers include DDX_Text, DDV_, UpdateData, DoDataExchange, 控件绑定成员变量.
agent_created: true
---

# MFC 控件绑定 → Qt 方式

## Overview

把 MFC 的 `DoDataExchange()` / `DDX_*` / `DDV_*` / `UpdateData()` 机制改为 Qt 方式：**删除控件类型成员变量，统一用 `.ui` 的 `ui->xxx` 访问控件；只保留必要的值类型成员，用信号或显式读写函数在控件与数据间同步。**

## Guardrails

- **必须删除**控件类型成员：`CButton m_btnOk;`、`CEdit m_editName;`、`CListCtrl m_list;` 等。这类对象在 Qt 中由 `.ui` 拥有，通过 `ui->btnOk` 等访问，不另建成员。
- **只保留值类型成员**：真正参与业务逻辑的数据（如 `QString m_name;`、`int m_type;`），且仅在跨函数/跨窗口需要时保留。
- 不保留 `DoDataExchange()`、`UpdateData()`、任何 `DDX_*`/`DDV_*` 宏。
- `.ui` 控件的 objectName 必须稳定；`ui->` 引用与 objectName 一一对应。
- 校验在输入时（QValidator / 范围约束）或提交前显式执行，不依赖隐藏的数据交换框架。

## Workflow

1. **识别绑定与读取配置**：先读 `<项目根>/.mfc-qt/config.json` 的 `controlMap`（用 `../mfc-to-qt-migration/scripts/migration_config.py map list` 查看生效表），再扫描 `DoDataExchange()` 中每条 `DDX_*`，分成两类：
   - 控件类型绑定（`DDX_Control` 到 `CButton`/`CEdit`/`CListCtrl` 等）→ 删除成员，改 `ui->`。
   - 值类型绑定（`DDX_Text` 到 `CString`/`int`/`BOOL` 等）→ 决定用信号直连还是保留值成员。
2. **删除控件成员**：从头文件移除声明；所有原成员调用替换为 `ui->objectName`。查 `references/ddx-to-qt.md` 的替换表。
3. **选择同步策略**（见下节）。
4. **迁移校验**：`DDV_*` → QValidator / `setMaxLength` / `QSpinBox::setRange` / 提交前校验并提示。
5. **替换 UpdateData**：`UpdateData(TRUE)` → 从控件读取到数据；`UpdateData(FALSE)` → 把数据写回控件。
6. **验证**：初始值与 MFC 一致；编辑后数据正确；提交校验行为一致；无悬空 `ui->` 引用。

## Sync Strategy

| 场景 | 推荐做法 |
|---|---|
| 简单的"打开时显示、提交时读取" | 不设值成员；`writeToUi()` 从数据源填入，`onOk()` 直接 `ui->edit->text()` 读取 |
| 需要跨函数/跨窗口共享的数据 | 保留值成员，用 `textChanged` 等信号同步：`connect(ui->edit, &QLineEdit::textChanged, this, [this](const QString &s){ m_name = s; })` |
| 表单数据较多、结构清晰 | 定义结构体/DTO（如 `struct LoginData { QString user; int type; };`），`readFromUi()` 返回 DTO，`writeToUi(const DTO&)` 填入 |
| model/view 场景 | 用 `QDataWidgetMapper` 把字段映射到 model，减少手工同步 |
| 需要撤销/重做 | QUndoStack + 命令对象，值成员纳入命令 |

优先**不引入镜像状态**：能在提交时直接从 `ui->` 读取就不要再存一份成员，避免双份数据不一致。

## Before / After Example

```cpp
// ---- MFC ----
class CLoginDlg : public CDialogEx {
    CString m_strUser;   // 值绑定
    CEdit   m_editUser;  // 控件绑定（需删除）
    CButton m_btnOk;     // 控件绑定（需删除）
    virtual void DoDataExchange(CDataExchange* pDX) {
        DDX_Text(pDX, IDC_EDIT_USER, m_strUser);
        DDX_Control(pDX, IDC_EDIT_USER, m_editUser);
        DDX_Control(pDX, IDC_BTN_OK, m_btnOk);
        DDV_MaxChars(pDX, m_strUser, 32);
    }
    void OnOK() { UpdateData(TRUE); /* 使用 m_strUser */ }
};

// ---- Qt ----
class LoginDialog : public QDialog {
    Ui::LoginDialog *ui;
    // 不保留 m_editUser / m_btnOk；也不需要 m_strUser（提交时直接读）
    void accept() override {
        const QString user = ui->editUser->text().trimmed();
        if (user.isEmpty()) { /* 提示 */ return; }
        emit loginRequested(user);
        QDialog::accept();
    }
};
LoginDialog::LoginDialog(QWidget *parent) : QDialog(parent), ui(new Ui::LoginDialog) {
    ui->setupUi(this);
    ui->editUser->setMaxLength(32);           // 原 DDV_MaxChars
    connect(ui->buttonBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(ui->buttonBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
}
```

## Common Mistakes

- 保留控件类型成员并 `new QPushButton` 再 `setGeometry` 到 `.ui` 之上，造成重复控件。
- 把 `ui` 指针与控件成员混用，导致状态不同步。
- 在构造函数中调用 `readFromUi()` 但 `.ui` 尚未 `setupUi()`，读到空值或崩溃。
- 保留 `UpdateData(TRUE/FALSE)` 命名的空壳函数，语义不清。
- 校验只做提示但允许提交，行为与 MFC `DDV` 失败时不一致。

## Bundled References

- `references/ddx-to-qt.md`：DDX/DDV 逐项替换表与 DTO 模式。
- `references/validation-patterns.md`：校验与错误提示做法。

## Output Shape

1. 绑定清单（原 DDX/DDV 项、类型、处理决策）
2. 删除的控件成员列表与 `ui->` 替换映射
3. 同步策略说明与数据对象/DTO 定义
4. 校验规则迁移表
5. 修改后的 `.h` / `.cpp` 片段

## Qt 版本与自定义控件映射

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor` 与 `controlMap`。用户自定义的 MFC 控件 → Qt widget 对应关系优先于内置默认表，映射变更须用 `../mfc-to-qt-migration/scripts/migration_config.py map add` 存盘。
- validator 统一用 `QRegularExpressionValidator` / `QIntValidator` / `QDoubleValidator`，不新写 `QRegExpValidator`（Qt 6 已移除）。
- `QVariant` 类型判断、`QStringView` 等差异按 `../mfc-to-qt-migration/references/qt-version-compat.md` 选择写法。
- 数据成员仍用值类型 + `readFromUi()`/`writeToUi()`，与 widget 类型映射无关。

Prefer Chinese explanations when the user writes in Chinese.
