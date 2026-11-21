# 校验与错误提示

## DDV → Qt 机制对照

| MFC DDV | Qt 机制 | 时机 |
|---|---|---|
| `DDV_MaxChars(pDX, s, n)` | `ui->edit->setMaxLength(n)` | 输入时拦截 |
| `DDV_MinMaxInt(pDX, n, lo, hi)` | `QSpinBox::setRange(lo, hi)` 或 `QIntValidator(lo, hi, this)` | 输入时/提交时 |
| `DDV_MinMaxDouble` | `QDoubleSpinBox::setRange` / `QDoubleValidator` | 输入时 |
| `DDV_MinMaxUInt` | `QSpinBox`（非负范围）/ `QRegularExpressionValidator` | 输入时 |
| 自定义格式校验 | `QRegularExpressionValidator` | 输入时 |
| 必填校验 | 提交时判空 + 提示 | 提交时 |
| 跨字段校验（如两次密码一致） | 提交时 `validateInput()` | 提交时 |

## 输入时校验

```cpp
// 长度
ui->editName->setMaxLength(32);

// 整数范围
ui->editPort->setValidator(new QIntValidator(1, 65535, this));

// 正则（如只允许字母数字下划线）
auto *rx = new QRegularExpressionValidator(
    QRegularExpression(QStringLiteral("^[A-Za-z0-9_]+$")), this);
ui->editCode->setValidator(rx);
```

用 `QLineEdit::setValidator()` 可即时阻止非法输入；需要给用户输入反馈时，配合 `QToolTip::showText()` 在 `textChanged` 中提示。

## 提交前校验

```cpp
bool LoginDialog::validateInput(QString *error) const {
    if (ui->editUser->text().trimmed().isEmpty()) {
        *error = tr("用户名不能为空");
        return false;
    }
    if (ui->editPass->text().isEmpty()) {
        *error = tr("密码不能为空");
        return false;
    }
    return true;
}

void LoginDialog::accept() {
    QString error;
    if (!validateInput(&error)) {
        QMessageBox::warning(this, tr("输入错误"), error);
        return;                       // 与 MFC DDV 失败一致：不关闭对话框
    }
    emit loginRequested(readFromUi());
    QDialog::accept();
}
```

关键点：校验失败时**不要**调用基类 `accept()`，保持对话框打开，与 MFC `UpdateData(TRUE)` 返回 FALSE 的行为一致。

## 错误提示方式

| 场景 | Qt 做法 |
|---|---|
| 单个字段格式错误 | `QToolTip::showText()` + 字段红框（QSS 或 `setProperty("error", true)` 后 `style()->polish()`） |
| 整体提交失败 | `QMessageBox::warning` |
| 长表单错误汇总 | 在表单顶部放 `QLabel` 汇总，或 `QListWidget` 列出所有错误 |
| 状态栏提示 | 主窗口 `statusBar()->showMessage()` |

## 与按钮状态联动

MFC `ON_UPDATE_COMMAND_UI` 常用于"输入合法才启用 OK 按钮"，Qt 中：

```cpp
auto updateOkEnabled = [this]() {
    ui->buttonBox->button(QDialogButtonBox::Ok)
        ->setEnabled(!ui->editUser->text().trimmed().isEmpty());
};
connect(ui->editUser, &QLineEdit::textChanged, this, updateOkEnabled);
updateOkEnabled();   // 初始状态也要设置
```

避免用 `QTimer` 周期性轮询；在相关 `textChanged`/`currentIndexChanged` 时更新即可。
