# 信号槽连接表模板

每个迁移的窗口维护一张连接表，作为改造记录与回归依据。放在源码注释或随窗口的 `docs/` 中均可。

## 表格模板

| # | 原 MFC 宏 | 发送者 objectName | Qt 信号 | 接收者/槽 | 参数适配 | 状态 |
|---|---|---|---|---|---|---|
| 1 | `ON_BN_CLICKED(IDC_BTN_OK)` | `btnOk` | `clicked(bool)` | `onOkClicked()` | 无 | 已验证 |
| 2 | `ON_EN_CHANGE(IDC_EDIT_USER)` | `editUser` | `textChanged(QString)` | `onUserChanged(QString)` | 直接 | 已验证 |
| 3 | `ON_CBN_SELCHANGE(IDC_COMBO_TYPE)` | `comboType` | `currentIndexChanged(int)` | `onTypeChanged(int)` | `QOverload<int>::of` | 待验证 |
| 4 | `ON_COMMAND(ID_FILE_OPEN)` | `actionFileOpen` | `triggered(bool)` | `openFile()` | 无 | 已验证 |

## 维护约定

- **连接位置集中**：优先在构造函数 `setupUi()` 之后，或统一的 `connectSignals()` 方法中，便于与表格核对。
- **objectName 即契约**：表格中的发送者名必须与 `.ui` 中 objectName 完全一致。
- **状态标记**：`待验证` → `已验证` → `已移除`（原宏确认无对应需求）。
- **重复连接**：对可能被多次调用的连接函数，使用 `Qt::UniqueConnection`，或在连接前断开旧连接。
- **断开时机**：动态创建的发送者销毁时 Qt 自动断开；手动 `disconnect` 仅用于切换行为，避免遗漏。

## 重载信号消歧示例

```cpp
// Qt 5（需要 QOverload）
connect(ui->comboType, QOverload<int>::of(&QComboBox::currentIndexChanged),
        this, &MyDialog::onTypeChanged);

// Qt 6（qOverload 更简洁）
connect(ui->spinBox, qOverload<int>(&QSpinBox::valueChanged),
        this, &MyDialog::onValueChanged);
```

## 检查项

- [ ] 表格中每条宏都有对应连接或注明"已移除"及原因。
- [ ] 所有连接使用新语法，无 `SIGNAL()`/`SLOT()` 字符串。
- [ ] 重载信号已消歧，能编译通过。
- [ ] 状态列全部为"已验证"或"已移除"后才算改造完成。
