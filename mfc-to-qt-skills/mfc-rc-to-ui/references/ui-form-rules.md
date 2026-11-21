# .ui 表单生成规则

## 合法骨架

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>LoginDialog</class>
 <widget class="QDialog" name="LoginDialog">
  <property name="windowTitle">
   <string>登录</string>
  </property>
  <layout class="QVBoxLayout" name="verticalLayout">
   <item>
    <widget class="QLineEdit" name="editUser">
     <property name="mfcId"><string>IDC_EDIT_USER</string></property>
     <property name="placeholderText"><string>用户名</string></property>
    </widget>
   </item>
   <item>
    <widget class="QDialogButtonBox" name="buttonBox">
     <property name="standardButtons">
      <set>QDialogButtonBox::Ok|QDialogButtonBox::Cancel</set>
     </property>
    </widget>
   </item>
  </layout>
 </widget>
 <resources>
  <include location="resources/app.qrc"/>
 </resources>
 <connections/>
</ui>
```

- 根元素必须是 `<ui version="4.0">`，含 `<class>`、`<widget>`、`<resources>`、`<connections>`。
- `<class>` 与顶层 `<widget name="...">` 必须与 C++ 包装类同名。
- `QDialogButtonBox` 的 `standardButtons` 用 `<set>Enum::A|Enum::B</set>` 语法。

## objectName 命名约定

| MFC ID | objectName |
|---|---|
| `IDC_EDIT_USER` | `editUser` |
| `IDC_BTN_OK` | `btnOk` |
| `IDC_COMBO_TYPE` | `comboType` |
| `IDC_LIST_RESULT` | `listResult` |
| `IDC_STATIC_STATUS` | `labelStatus` |
| `IDD_LOGIN_DIALOG` | class 名 `LoginDialog` |
| `ID_FILE_OPEN` | `actionFileOpen` |

规则：去掉 `IDC_`/`ID_` 前缀，按语义转驼峰；同名前缀保持类型前缀（`btn`/`edit`/`combo`/`list`/`label`/`check`/`radio`/`action`）。objectName 一旦确定即为稳定契约，不要随重构改名。

## mfcId 动态属性

为每个由 MFC 控件转换来的 widget 保留原始 ID，便于消息映射改造与回溯：

```xml
<property name="mfcId"><string>IDC_EDIT_USER</string></property>
```

C++ 中可读取：`widget->property("mfcId").toString()`。该属性不参与运行逻辑，仅作迁移辅助。

## 布局转换模式

- **表单区**（标签 + 输入框成对）→ `QFormLayout`，标签使用 QLabel 的 buddy 关系。
- **按钮行** → `QHBoxLayout`，末尾加 `QSpacerItem` 或 stretch 把按钮推到右侧。
- **分组框** → `QGroupBox` 作为容器，内部结构再用嵌套布局。
- **主区域 + 侧栏** → `QHBoxLayout` + stretch factor（如 1:4）。
- **可切换页面** → `QStackedWidget`。
- **可拖拽分隔** → `QSplitter`。
- **大量数据表格** → `QTableView` + model，不在 `.ui` 中塞入成千 widget。

每个布局显式设置合理的 `margin`/`spacing` 或交由 Qt 默认，避免依赖绝对坐标。

## 属性设置要点

- `windowTitle` 用 `<string>`，需要翻译的文本不要写 `notr="true"`（除非确为代码/数字）。
- 初始文本、tooltip、placeholder 使用 `<string>` 包裹，便于 `lupdate` 提取。
- `enabled=false` / `readOnly=true` / `checkable` 等状态与 MFC `WS_*`、`ES_*`、`BS_*` 对齐。
- Tab 顺序：`.ui` 中 widget 出现顺序即 Tab 顺序；必要时在 C++ 中 `setTabOrder()`。
- 自绘/自定义控件用 **promoted widget**：`<customwidget>` 声明 header 与 extends，不要改回 QWidget。

## 校验

生成后用以下方式确认：

1. Qt Designer 打开无解析错误。
2. `uic form.ui -o ui_form.h` 能成功生成头文件（或直接由 CMake AUTOUIC 编译）。
3. 编译产物中控件指针名称与 `ui->xxx` 引用一致。
