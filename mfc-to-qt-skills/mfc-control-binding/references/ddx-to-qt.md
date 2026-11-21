# DDX/DDV → Qt 替换明细

## DDX 逐项替换

| MFC DDX | 变量类型 | Qt 做法 |
|---|---|---|
| `DDX_Text(id, CString s)` | 文本 | `ui->edit->text()`；或 `QString` 成员 + `textChanged` 同步 |
| `DDX_Text(id, int n)` | 数值 | `ui->edit->text().toInt()`；优先直接用 `QSpinBox::value()` |
| `DDX_Text(id, double d)` | 数值 | `ui->edit->text().toDouble()`；优先 `QDoubleSpinBox::value()` |
| `DDX_Check(id, int n)` | 勾选 | `ui->check->checkState()` / `isChecked()` |
| `DDX_Radio(id, int n)` | 单选组 | `QButtonGroup::checkedId()`；为按钮设置 `setId()` |
| `DDX_CBIndex(id, int n)` | 组合索引 | `ui->combo->currentIndex()` |
| `DDX_CBString(id, CString s)` | 组合文本 | `ui->combo->currentText()` |
| `DDX_LBIndex(id, int n)` | 列表索引 | `ui->list->currentRow()` |
| `DDX_LBString(id, CString s)` | 列表文本 | `ui->list->currentItem()->text()` |
| `DDX_Scroll(id, int n)` | 滚动位置 | `ui->scrollBar->value()` / `ui->slider->value()` |
| `DDX_Control(id, CButton/CWnd obj)` | 控件 | **删除成员**，用 `ui->objectName` |
| `DDX_Control(id, CListCtrl list)` | 控件 | **删除成员**，用 `ui->tableView` / `ui->treeWidget` + model |
| `DDX_Control(id, CComboBox combo)` | 控件 | **删除成员**，用 `ui->combo` |

判断原则：变量名以 `m_` 开头且类型是 `C*` 控件类 → 控件绑定，删除；类型是 `CString`/`int`/`BOOL`/`double`/枚举 → 值绑定，按表处理。

## UpdateData 替换

| MFC | Qt |
|---|---|
| `UpdateData(TRUE)` | 从控件读取：`const QString s = ui->edit->text();` 或 `DTO d = readFromUi();` |
| `UpdateData(FALSE)` | 写回控件：`ui->edit->setText(s);` 或 `writeToUi(d);` |
| `UpdateData()` 默认 TRUE | 按读取处理 |
| 返回值（校验失败返回 FALSE） | 自定义 `bool validateInput(QString *error)`，失败时提示并中止提交 |

不要保留名为 `UpdateData` 的函数来"模拟" MFC 行为；改用语义清晰的方法名。

## DTO / 结构体模式

当字段较多或需要跨窗口传递时使用：

```cpp
struct UserFormData {
    QString name;
    int type = 0;
    bool enabled = false;
};

UserFormData LoginDialog::readFromUi() const {
    return {
        ui->editName->text().trimmed(),
        ui->comboType->currentIndex(),
        ui->checkEnabled->isChecked()
    };
}

void LoginDialog::writeToUi(const UserFormData &d) {
    ui->editName->setText(d.name);
    ui->comboType->setCurrentIndex(d.type);
    ui->checkEnabled->setChecked(d.enabled);
}
```

调用方：`writeToUi(data)` 在初始化时；`const auto data = readFromUi()` 在提交时。

## QDataWidgetMapper 模式

表单字段直接对应 model 列时：

```cpp
mapper = new QDataWidgetMapper(this);
mapper->setModel(model);
mapper->addMapping(ui->editName, NameColumn);
mapper->addMapping(ui->comboType, TypeColumn);
mapper->toFirst();
// 提交：mapper->submit();
```

适合"表格选中行 → 编辑区显示 → 保存回模型"的场景，替代手工 DTO 同步。

## 控件成员替换速查

| 原成员调用 | Qt 替换 |
|---|---|
| `m_editUser.SetWindowText(_T("abc"))` | `ui->editUser->setText("abc")` |
| `m_editUser.GetWindowText(s)` | `QString s = ui->editUser->text()` |
| `m_editUser.SetReadOnly(TRUE)` | `ui->editUser->setReadOnly(true)` |
| `m_btnOk.EnableWindow(FALSE)` | `ui->btnOk->setEnabled(false)` |
| `m_btnOk.SetWindowText(_T("OK"))` | `ui->btnOk->setText("OK")` |
| `m_list.InsertString(0, _T("x"))` | `ui->list->insertItem(0, "x")` |
| `m_list.GetCurSel()` | `ui->list->currentRow()` |
| `m_combo.AddString(_T("x"))` | `ui->combo->addItem("x")` |
| `m_combo.GetCurSel()` | `ui->combo->currentIndex()` |
| `m_check.GetCheck()` | `ui->check->isChecked()` |
| `m_static.SetWindowText(_T("x"))` | `ui->label->setText("x")` |

## 字符串处理

- `CString` → `QString`；`_T("...")` → `"..."`（必要时 `QStringLiteral("...")`）。
- `s.GetLength()` → `s.length()`；`s.IsEmpty()` → `s.isEmpty()`。
- `s.Format(_T("%d"), n)` → `QString::number(n)` 或 `QStringLiteral("%1").arg(n)`。
- `strcpy`/`lstrcpy` 到固定缓冲 → 直接用 QString，无需字符缓冲。
