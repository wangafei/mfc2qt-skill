# mfc2qt-skill

A set of AI coding-assistant Skills for **MFC → Qt Widgets** migration. They systematically convert MFC scenarios — `.rc` resources, message maps, DDX bindings, manual `OnSize` layout, geometry APIs, modal dialogs, keyboard/mouse messages, and more — into **Qt Widgets + `.ui` + signals & slots + modern CMake** implementations.

Modeled after the organization of `coczhang/qt-general-dev-skill` and `TheQtCompanyRnD/agent-skills`.

> 📖 For the full documentation (configuration, usage, scripts, and directory details), see [**mfc-to-qt-skills/README.en.md**](mfc-to-qt-skills/README.en.md).

## Structure

The skill package lives in the [`mfc-to-qt-skills/`](mfc-to-qt-skills/) directory and contains 10 skills: 1 main entry point + 9 specialized ones. Each skill consists of `SKILL.md` (entry/trigger rules), `references/` (mapping and rule details), optional `scripts/` (scanning/inference scripts), and `assets/` (templates).

| Skill | Responsibility |
|---|---|
| [`mfc-to-qt-migration`](mfc-to-qt-skills/mfc-to-qt-migration) | Main entry point: inventory, batching strategy, routing, global rules, acceptance checklist |
| [`mfc-rc-to-ui`](mfc-to-qt-skills/mfc-rc-to-ui) | `.rc` dialogs / menus / icons → `.ui` + `.qrc` |
| [`mfc-macro-to-slot`](mfc-to-qt-skills/mfc-macro-to-slot) | Message-map macros → new-syntax `connect()` |
| [`mfc-control-binding`](mfc-to-qt-skills/mfc-control-binding) | Remove control-typed member bindings; use `ui->` + value members / QValidator |
| [`mfc-layout-onsize`](mfc-to-qt-skills/mfc-layout-onsize) | Manual `OnSize` rearrangement → QLayout, with automatic inference of layout intent |
| [`mfc-message-to-slot`](mfc-to-qt-skills/mfc-message-to-slot) | `ON_MESSAGE` / `SendMessage` / `PostMessage` → signals & slots / QEvent |
| [`mfc-geometry-api`](mfc-to-qt-skills/mfc-geometry-api) | `MoveWindow` / `GetWindowRect` / coordinate conversion → Qt geometry APIs |
| [`mfc-dialog-lifecycle`](mfc-to-qt-skills/mfc-dialog-lifecycle) | Modal / modeless → `exec()` / `open()` / `show()` and ownership |
| [`mfc-input-events`](mfc-to-qt-skills/mfc-input-events) | Keyboard / mouse messages → event handlers / `eventFilter` / `QShortcut` |
| [`mfc-to-qt-cmake`](mfc-to-qt-skills/mfc-to-qt-cmake) | CMake projects, AUTOMOC/AUTOUIC/AUTORCC, resources and translations |

## Key Features

- **Configurable Qt version**: Qt 5 / Qt 6 / a specific version / auto-detection. Configuration is centralized in `<project root>/.mfc-qt/config.json`, and the CMake templates support both major versions.
- **Persistable custom control mappings**: users can maintain their own MFC control → Qt widget mappings; project-level configuration takes precedence over global and built-in defaults.
- **OnSize layout intent inference**: infers left-center-right, top-bottom, and top + left-center-right layout trees from `MoveWindow`/`SetWindowPos` coordinate expressions, and outputs `.ui` skeleton suggestions.

## Quick Start

Copy the `mfc-*` directories under `mfc-to-qt-skills/` into your AI assistant's user-level skills directory (available globally), or into a project's skills directory (available only for that project). For example:

```
cp -R mfc-to-qt-skills/mfc-* <your skills directory>/
```

Then simply describe your scenario, for example:

```
Use mfc-to-qt-migration to inventory this MFC project, targeting Qt 5.15, and suggest migration batches.
Use mfc-rc-to-ui to convert IDD_LOGIN in Login.rc to .ui.
Use mfc-layout-onsize to analyze CMainDlg::OnSize and infer the layout pattern.
```

For more complete commands and documentation, see the [**detailed README**](mfc-to-qt-skills/README.en.md).

## License

See [LICENSE](LICENSE).
