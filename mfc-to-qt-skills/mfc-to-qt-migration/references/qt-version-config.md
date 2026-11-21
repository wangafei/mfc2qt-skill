# Qt 版本选择（不锁死版本）

本技能系列**不默认绑定某一个 Qt 大版本**。开始任何迁移前都要先确定目标版本，并把它写进项目配置，后续所有专项技能和 CMake 生成都读取同一份配置。

## 配置位置与优先级

| 层级 | 路径 | 用途 |
|---|---|---|
| 内置默认 | 技能内 `BUILTIN_MAP` | 仅在用户未配置时兜底 |
| 全局配置 | `~/.workbuddy/mfc-to-qt-skills/config.json` | 个人长期偏好，跨项目复用 |
| 项目配置 | `<项目根>/.mfc-qt/config.json` | 项目级决定，**优先于全局配置** |

字段按层级合并（不是整个文件替换）：项目配置只写需要覆盖的字段即可。

`.mfc-qt/config.json` 应提交到版本库，使团队与后续会话使用同一版本与映射表。

## 决策顺序

1. **用户显式指定** → 最高优先级。支持 `auto`、`5`、`6`、`5.15`、`6.5.3` 等写法。
2. **自动探测** → 扫描项目 `CMakeLists.txt` 的 `find_package(Qt5/Qt6 ...)`、Qt 相关环境变量、PATH 上的 `qmake`/`qmake6`。
3. **仍无法判定** → 必须向用户询问，不得自行假定 Qt 6。

```bash
S=~/.workbuddy/skills/mfc-to-qt-migration/scripts/migration_config.py

python "$S" init      --root <项目根>
python "$S" detect    --root <项目根>            # 只读探测，给出证据
python "$S" set-qt auto   --root <项目根>        # 使用探测结果
python "$S" set-qt 5.15   --root <项目根>        # 用户指定 Qt 5.15+
python "$S" set-qt 6      --root <项目根>        # 用户指定 Qt 6
python "$S" show --detect --root <项目根>
```

`detect` 只收集证据；若存在多个互相矛盾的证据（例如 CMake 写 Qt5 但 PATH 上是 Qt6 qmake），它返回 `ambiguous`，此时必须问用户。

## 配置结构

```json
{
  "schemaVersion": 1,
  "qt": {
    "requested": "5.15",
    "resolvedMajor": "5",
    "minVersion": "5.15",
    "components": ["Widgets"]
  },
  "controlMap": {
    "mygridctrl": {
      "widget": "QTableView",
      "header": "QtWidgets/QTableView",
      "note": "自研表格派生类",
      "source": "user"
    }
  }
}
```

- `resolvedMajor`：实际采用的 `5` 或 `6`，生成 CMake / 选择 API 写法时读它。
- `minVersion`：用户指定的最低版本，用于 `find_package(Qt5 5.15 REQUIRED ...)`。
- `components`：需要的 Qt 模块，默认 `Widgets`，按需要增加 `Network`、`Sql`、`Svg`、`Concurrent`、`Test` 等。

## 下游技能必须遵守

- 生成 CMake 时，用 `resolvedMajor` 决定 `find_package(QtN ...)` 和 `QtN::Widgets`，不允许出现硬编码 `Qt6::Widgets`。
- 写代码时，若 API 在 Qt5/Qt6 间有差异，按 `qt-version-compat.md` 选择写法；确实无法统一时给出两个版本分支并注明条件。
- `.ui` 文件格式在 Qt5/Qt6 之间兼容；不要写入版本专属属性。
- 用户改变版本后，重新检查已生成代码中的差异 API 与 CMake target。

## 交互话术

若用户未指定版本且探测失败，直接询问：

> 目标 Qt 版本是哪个？可选 Qt 5（最低 5.15）、Qt 6，或让我根据现有 CMake/qmake 自动判断。选定后会写入 `.mfc-qt/config.json`，后续技能统一遵守。
