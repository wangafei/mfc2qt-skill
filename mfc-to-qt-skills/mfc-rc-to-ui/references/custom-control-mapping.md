# 自定义控件对应关系（用户扩展 + 持久化）

内置的 `rc-control-mapping.md` 只覆盖标准 Win32/MFC 控件。项目里的第三方控件、自绘控件、派生类必须允许用户自行指定对应关系，并且**转换后保存到磁盘**，后续会话与其它技能继续复用。

## 配置文件

统一使用 `<项目根>/.mfc-qt/config.json` 的 `controlMap` 字段。该文件由总入口技能提供的脚本维护：

```bash
S=~/.workbuddy/skills/mfc-to-qt-migration/scripts/migration_config.py

python "$S" map list --root <项目根>                     # 查看生效表（内置 + 用户）
python "$S" map add MyGridCtrl QTableView --root <项目根>
python "$S" map add "MyDate Ctl" QDateEdit --header QtWidgets/QDateEdit --note "自研日期控件" --root <项目根>
python "$S" map remove MyGridCtrl --root <项目根>
python "$S" map export --root <项目根> --format json > mappings.json
python "$S" map import mappings.json --root <项目根>
```

- 不传 `--root` 时默认当前目录；`--scope global` 写入 `~/.workbuddy/mfc-to-qt-skills/config.json` 作为个人长期偏好。
- 项目级配置优先于全局配置；两者都覆盖内置默认表。
- token 归一化：去掉 `IDC_` 前缀、忽略大小写与非字母数字字符，因此 `IDC_MY_GRID` 与 `MyGrid` 不会自动等价——按实际出现的标记逐个登记。
- 映射条目可包含 `widget`（必需）、`header`、`note`、`source`。`source=user` 表示用户自定义。

## 何时必须写盘

遇到下列任一情况，都要先 `map add` 再继续生成 `.ui`：

1. `.rc` 的 `CONTROL` 使用了非标准窗口类（非 `SysListView32`、`SysTreeView32`、`msctls_*` 等）。
2. MFC 头文件中出现自定义控件类成员（`CMyGridCtrl m_grid;`），且目标 Qt widget 不是默认推断结果。
3. 用户明确说"这个控件我用 XXX 代替"或给出任何自定义对应关系。
4. 同一控件在多个对话框出现，映射结果必须保持一致。

不要只在回答里写"我把它映射成 QTableView"而不写盘——那样下一次迁移会重新推断并可能得到不同结果。

## 使用映射生成 .ui

1. 用 `map list` 得到生效表，把它作为本次转换的唯一依据。
2. 自定义 widget 若不是 Qt 标准类（例如项目自己的 `MyChartWidget`），`.ui` 中 `<widget class="MyChartWidget">` 仍可写，但必须在 `.pro`/CMake 中让 AUTOUIC 或手写 include 能找到该类的头文件；同时在 C++ 包装类中 include `header` 指定的路径。
3. 保留 `mfcId` 动态属性与稳定 `objectName`，映射只决定 widget 类型，不改变 ID 语义。
4. 若自定义 widget 需要额外属性（列数、数据源等），写进 `.ui` 的 `<property>` 或 C++ 初始化代码，并在 `note` 中记录理由。
5. 在输出中列出本次用到的所有 `source=user` 映射，方便用户核对。

## 冲突处理

- 用户映射与内置默认冲突 → 用户映射胜出，并在输出中说明"覆盖了内置默认"。
- 全局映射与项目映射冲突 → 项目映射胜出。
- 用户要求删除某条自定义映射 → `map remove`，之后恢复内置默认行为。
- 映射不确定时先询问用户，确认后立即写盘，不要猜测。

## 与 Qt 版本配置共存

同一个 `config.json` 同时保存 `qt` 和 `controlMap`。`map add` 只修改映射字段，不会覆盖已设定的 Qt 版本；`set-qt` 同理不会清除映射。完整配置结构见 `../../mfc-to-qt-migration/references/qt-version-config.md`。
