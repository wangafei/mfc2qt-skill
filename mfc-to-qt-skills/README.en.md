# MFC → Qt Migration Skills

[English](README.en.md) | [中文](README.md)

A set of AI assistant skills for migrating MFC (Microsoft Foundation Classes) desktop applications to **Qt Widgets**. Modeled after the organization of `coczhang/qt-general-dev-skill` and `TheQtCompanyRnD/agent-skills`.

Unified technical approach: **Qt Widgets + `.ui` forms + QSS + modern CMake**. No QML-based solutions are generated.

## Three Configurable Capabilities

1. **Qt version is not locked in**: supports Qt 5 / Qt 6 / a user-specified specific version / auto-detection. Configuration is stored in `<project root>/.mfc-qt/config.json`, and all skills and CMake templates read from the same configuration.
2. **Custom control mappings are persistent**: users can add their own MFC control → Qt widget mappings and save them with `map add`. Project-level configuration takes precedence over global configuration and the built-in default table.
3. **OnSize layout intent auto-inference**: parses `MoveWindow`/`SetWindowPos` coordinates into linear expressions, automatically recognizing patterns such as left-center-right, top-bottom, top + left-center-right, left + top-center-bottom, grid, and more — then outputs a layout tree and a `.ui` skeleton.

## Skill List (10)

| Skill | Responsibility | Typical Trigger |
|---|---|---|
| `mfc-to-qt-migration` | Main entry point: inventory, strategy, routing, global rules, acceptance checklist | MFC migration to Qt, MFC to Qt |
| `mfc-rc-to-ui` | `.rc` dialogs / menus / resources → `.ui` + `.qrc` | rc to ui, DIALOGEX, IDC_ controls |
| `mfc-macro-to-slot` | Message-map macros → new-syntax `connect()` | ON_BN_CLICKED, BEGIN_MESSAGE_MAP |
| `mfc-control-binding` | Remove control-typed member bindings; use `ui->` + value members / validation | DDX_Text, UpdateData, DoDataExchange |
| `mfc-layout-onsize` | Manual `OnSize` rearrangement → QLayout | OnSize, WM_SIZE, resize with window |
| `mfc-message-to-slot` | Custom messages / SendMessage / PostMessage → signals & slots / QEvent | ON_MESSAGE, WM_USER, SendMessage |
| `mfc-geometry-api` | MoveWindow / GetWindowRect / coordinate conversion → Qt geometry APIs | MoveWindow, SetWindowPos, GetWindowRect |
| `mfc-dialog-lifecycle` | Modal / modeless → exec() / open() / show() + ownership | DoModal, modeless, EndDialog |
| `mfc-input-events` | Keyboard / mouse messages → event handlers / eventFilter / shortcuts | PreTranslateMessage, WM_KEYDOWN, OnMouseMove |
| `mfc-to-qt-cmake` | CMake projects, AUTOUIC/AUTORCC, resources and translations | CMakeLists.txt, AUTOUIC, migrate CMake |

## Directory Structure

```text
mfc-to-qt-skills/
├── README.md
├── mfc-to-qt-migration/          # main entry point
│   ├── SKILL.md
│   ├── references/
│   │   ├── mfc-qt-mapping.md
│   │   ├── qt-version-config.md
│   │   ├── qt-version-compat.md
│   │   └── migration-checklist.md
│   └── scripts/mfc_scan.py, migration_config.py
├── mfc-rc-to-ui/
│   ├── SKILL.md
│   ├── references/
│   │   ├── rc-control-mapping.md
│   │   ├── ui-form-rules.md
│   │   └── custom-control-mapping.md
│   └── scripts/rc_inventory.py
├── mfc-macro-to-slot/
│   ├── SKILL.md
│   └── references/macro-mapping.md, connection-table.md
├── mfc-control-binding/
│   ├── SKILL.md
│   └── references/ddx-to-qt.md, validation-patterns.md
├── mfc-layout-onsize/
│   ├── SKILL.md
│   ├── references/onsize-patterns.md, layout-patterns.md,
│   │   intent-inference.md, layout-api-notes.md
│   └── scripts/onsize_layout_infer.py
├── mfc-message-to-slot/
│   ├── SKILL.md
│   └── references/message-conversion.md, send-post-mapping.md
├── mfc-geometry-api/
│   ├── SKILL.md
│   └── references/geometry-mapping.md, coordinate-systems.md
├── mfc-dialog-lifecycle/
│   ├── SKILL.md
│   └── references/modal-modeless.md, lifecycle-events.md
├── mfc-input-events/
│   ├── SKILL.md
│   └── references/keyboard-mapping.md, mouse-mapping.md
└── mfc-to-qt-cmake/
    ├── SKILL.md
    ├── assets/CMakeLists.txt
    └── references/common-mistakes.md, project-structure.md
```

## Installation

Copy the `mfc-*` directories into your AI assistant's user-level skills directory to use them across all projects. To reinstall:

```bash
cp -R mfc-to-qt-skills/mfc-* <your skills directory>/
```

If you only need them for a specific project, copy them into that project's own skills directory instead.

## Recommended Usage

Simply describe your migration scenario and the assistant will automatically trigger the corresponding skill based on its `description`; you can also specify one explicitly:

```text
Use mfc-to-qt-migration to inventory this MFC project, targeting Qt 5.15, and suggest migration batches.
Use mfc-rc-to-ui to convert IDD_LOGIN in Login.rc to .ui, map the custom MyGridCtrl to QTableView, and save the mapping.
Use mfc-layout-onsize to analyze CMainDlg::OnSize, infer a left-center-right layout, and generate a .ui skeleton.
Use mfc-to-qt-cmake to generate CMakeLists.txt according to the project configuration.
```

For complex migrations, start with `mfc-to-qt-migration`; it routes to the specialized skills in a fixed order to avoid rework.

## Scripts

The four scripts depend only on the Python 3 standard library. Scanning and inference outputs are **hints/suggestions** and must be verified manually against the source code:

```bash
# 1) Version and custom mapping configuration (writes to .mfc-qt/config.json)
python mfc-to-qt-migration/scripts/migration_config.py init --root <project root>
python mfc-to-qt-migration/scripts/migration_config.py detect --root <project root>
python mfc-to-qt-migration/scripts/migration_config.py set-qt auto --root <project root>  # or 5.15 / 6
python mfc-to-qt-migration/scripts/migration_config.py map add MyGridCtrl QTableView --root <project root>
python mfc-to-qt-migration/scripts/migration_config.py map list --root <project root>

# 2) MFC pattern scanning
python mfc-to-qt-migration/scripts/mfc_scan.py
python mfc-to-qt-migration/scripts/mfc_scan.py --json

# 3) .rc resource inventory
python mfc-rc-to-ui/scripts/rc_inventory.py
python mfc-rc-to-ui/scripts/rc_inventory.py --json

# 4) OnSize layout intent inference
python mfc-layout-onsize/scripts/onsize_layout_infer.py --root <project root>
python mfc-layout-onsize/scripts/onsize_layout_infer.py --root <project root> --ui-out layout.xml
```

When `--root` is omitted, the current directory is used by default; `--scope global` stores version preferences or mappings as personal global configuration.

## Verification

All `SKILL.md` files pass skill-creator's `quick_validate.py` validation; all four scripts were tested and passed with synthetic MFC samples.
