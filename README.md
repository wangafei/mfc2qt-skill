# mfc2qt-skill

一组面向 **MFC → Qt Widgets** 迁移的 [WorkBuddy](https://www.workbuddy.cn/) Skill，把 MFC 的 `.rc` 资源、消息映射、DDX 绑定、`OnSize` 手工布局、几何 API、模态窗体、键鼠消息等场景，系统性转换为 **Qt Widgets + `.ui` + 信号槽 + 现代 CMake** 的实现。

参考 `coczhang/qt-general-dev-skill` 与 `TheQtCompanyRnD/agent-skills` 的组织方式制作。

> 📖 完整说明（配置、用法、脚本、目录细节）见 **[mfc-to-qt-skills/README.md](mfc-to-qt-skills/README.md)**。

## 结构

技能包位于 [`mfc-to-qt-skills/`](mfc-to-qt-skills/) 目录，共 10 个技能：1 个总入口 + 9 个专项。每个技能由 `SKILL.md`（入口/触发规则）、`references/`（映射与规则细节）、按需的 `scripts/`（扫描/推断脚本）和 `assets/`（模板）组成。

| 技能 | 职责 |
|---|---|
| [`mfc-to-qt-migration`](mfc-to-qt-skills/mfc-to-qt-migration/) | 总入口：盘点、分批策略、路由、全局规则、验收清单 |
| [`mfc-rc-to-ui`](mfc-to-qt-skills/mfc-rc-to-ui/) | `.rc` 对话框/菜单/图标 → `.ui` + `.qrc` |
| [`mfc-macro-to-slot`](mfc-to-qt-skills/mfc-macro-to-slot/) | 消息映射宏 → 新语法 `connect()` |
| [`mfc-control-binding`](mfc-to-qt-skills/mfc-control-binding/) | 删除控件类型成员绑定，改 `ui->` + 值成员/QValidator |
| [`mfc-layout-onsize`](mfc-to-qt-skills/mfc-layout-onsize/) | `OnSize` 手工重排 → QLayout，支持布局意图自动推断 |
| [`mfc-message-to-slot`](mfc-to-qt-skills/mfc-message-to-slot/) | `ON_MESSAGE` / `SendMessage` / `PostMessage` → 信号槽 / QEvent |
| [`mfc-geometry-api`](mfc-to-qt-skills/mfc-geometry-api/) | `MoveWindow` / `GetWindowRect` / 坐标换算 → Qt 几何接口 |
| [`mfc-dialog-lifecycle`](mfc-to-qt-skills/mfc-dialog-lifecycle/) | 模态/非模态 → `exec()` / `open()` / `show()` 与所有权 |
| [`mfc-input-events`](mfc-to-qt-skills/mfc-input-events/) | 键鼠消息 → 事件处理器 / `eventFilter` / `QShortcut` |
| [`mfc-to-qt-cmake`](mfc-to-qt-skills/mfc-to-qt-cmake/) | CMake 工程、AUTOMOC/AUTOUIC/AUTORCC、资源与翻译 |

## 主要特性

- **Qt 版本可配置**：Qt 5 / Qt 6 / 指定版本 / 自动探测，配置统一落在 `<项目根>/.mfc-qt/config.json`，CMake 模板同时支持两个大版本。
- **自定义控件映射可存盘**：用户可自行维护 MFC 控件 → Qt widget 的对应关系，项目级优先于全局与内置默认表。
- **OnSize 布局意图推断**：从 `MoveWindow`/`SetWindowPos` 的坐标算式推断左中右、上下、上+左中右等布局树，并输出 `.ui` 骨架建议。

## 快速开始

把 `mfc-to-qt-skills/` 下的 `mfc-*` 目录复制到 `~/.workbuddy/skills/`（全局可用），或复制到项目的 `.workbuddy/skills/`（仅该项目可用）：

```bash
cp -R mfc-to-qt-skills/mfc-* ~/.workbuddy/skills/
```

然后直接描述场景，例如：

```text
用 mfc-to-qt-migration 盘点这个 MFC 项目，目标 Qt 5.15，给出迁移批次建议。
用 mfc-rc-to-ui 把 Login.rc 的 IDD_LOGIN 转成 .ui。
用 mfc-layout-onsize 分析 CMainDlg::OnSize 推断布局模式。
```

更完整的命令与说明见 **[详细 README](mfc-to-qt-skills/README.md)**。

## License

见 [LICENSE](LICENSE)。
