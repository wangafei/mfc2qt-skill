# MFC → Qt 迁移技能系列

[English](README.en.md) | [中文](README.md)

面向 MFC（Microsoft Foundation Classes）桌面程序迁移到 **Qt Widgets** 的一组 AI 助手技能。参考 `coczhang/qt-general-dev-skill` 与 `TheQtCompanyRnD/agent-skills` 的组织方式制作。

统一技术路线：**Qt Widgets + `.ui` 表单 + QSS + 现代 CMake**。不生成 QML 方案。

## 三项可配置能力

1. **Qt 版本不锁死**：支持 Qt 5 / Qt 6 / 用户指定具体版本 / 自动探测，配置落在 `<项目根>/.mfc-qt/config.json`，所有技能与 CMake 模板读取同一份配置。
2. **自定义控件映射可持久化**：用户可自行增加 MFC 控件 → Qt widget 的对应关系，通过 `map add` 存盘；项目级配置优先于全局配置与内置默认表。
3. **OnSize 布局意图自动推断**：把 `MoveWindow`/`SetWindowPos` 的坐标解析成线性算式，自动识别左中右、上下、上+左中右、左+上中下、网格等模式，输出布局树与 `.ui` 骨架。

## 技能清单（10 个）

| 技能 | 职责 | 典型触发 |
|---|---|---|
| `mfc-to-qt-migration` | 总入口：盘点、策略、路由、全局规则、验收清单 | MFC 迁移 Qt、MFC 转 Qt |
| `mfc-rc-to-ui` | `.rc` 对话框/菜单/资源 → `.ui` + `.qrc` | rc 转 ui、DIALOGEX、IDC_ 控件 |
| `mfc-macro-to-slot` | 消息映射宏 → 新语法 `connect()` | ON_BN_CLICKED、BEGIN_MESSAGE_MAP |
| `mfc-control-binding` | 删除控件类型成员绑定，改 `ui->` + 值成员/校验 | DDX_Text、UpdateData、DoDataExchange |
| `mfc-layout-onsize` | `OnSize` 手工重排 → QLayout | OnSize、WM_SIZE、随窗口缩放 |
| `mfc-message-to-slot` | 自定义消息 / SendMessage / PostMessage → 信号槽 / QEvent | ON_MESSAGE、WM_USER、SendMessage |
| `mfc-geometry-api` | MoveWindow / GetWindowRect / 坐标换算 → Qt 几何接口 | MoveWindow、SetWindowPos、GetWindowRect |
| `mfc-dialog-lifecycle` | 模态/非模态 → exec()/open()/show() + 所有权 | DoModal、非模态、EndDialog |
| `mfc-input-events` | 键鼠消息 → 事件处理器 / eventFilter / 快捷键 | PreTranslateMessage、WM_KEYDOWN、OnMouseMove |
| `mfc-to-qt-cmake` | CMake 工程、AUTOUIC/AUTORCC、资源与翻译 | CMakeLists.txt、AUTOUIC、迁移 CMake |

## 目录结构

```text
mfc-to-qt-skills/
├── README.md
├── mfc-to-qt-migration/        # 总入口
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
│   │           intent-inference.md, layout-api-notes.md
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

## 安装

把 `mfc-*` 目录复制到所用 AI 助手的用户级技能目录，即可在所有项目中使用。若需重装：

```bash
cp -R mfc-to-qt-skills/mfc-* <你的技能目录>/
```

若只需在特定项目使用，复制到该项目自己的技能目录即可。

## 推荐用法

直接描述迁移场景，助手会按 description 自动触发对应技能；也可以显式指定：

```text
用 mfc-to-qt-migration 盘点这个 MFC 项目，目标 Qt 5.15，给出迁移批次建议。
用 mfc-rc-to-ui 把 Login.rc 里的 IDD_LOGIN 转成 .ui，自研 MyGridCtrl 映射成 QTableView 并存盘。
用 mfc-layout-onsize 分析 CMainDlg::OnSize，推断左中右布局并生成 .ui 骨架。
用 mfc-to-qt-cmake 按项目配置生成 CMakeLists.txt。
```

复杂迁移从 `mfc-to-qt-migration` 开始，它会按固定顺序路由到各专项技能，避免返工。

## 脚本

四个脚本只依赖 Python 3 标准库。扫描与推断输出均为**线索/建议**，需人工核对源码：

```bash
# 1) 版本与自定义映射配置（会写盘到 .mfc-qt/config.json）
python mfc-to-qt-migration/scripts/migration_config.py init --root <项目根>
python mfc-to-qt-migration/scripts/migration_config.py detect --root <项目根>
python mfc-to-qt-migration/scripts/migration_config.py set-qt auto --root <项目根>   # 或 5.15 / 6
python mfc-to-qt-migration/scripts/migration_config.py map add MyGridCtrl QTableView --root <项目根>
python mfc-to-qt-migration/scripts/migration_config.py map list --root <项目根>

# 2) MFC 模式扫描
python mfc-to-qt-migration/scripts/mfc_scan.py <mfc项目根目录>
python mfc-to-qt-migration/scripts/mfc_scan.py <mfc项目根目录> --json

# 3) .rc 资源盘点
python mfc-rc-to-ui/scripts/rc_inventory.py <app.rc>
python mfc-rc-to-ui/scripts/rc_inventory.py <app.rc> --json

# 4) OnSize 布局意图推断
python mfc-layout-onsize/scripts/onsize_layout_infer.py <MyDlg.cpp> --root <项目根>
python mfc-layout-onsize/scripts/onsize_layout_infer.py <MyDlg.cpp> --root <项目根> --ui-out layout.xml
```

不传 `--root` 时默认当前目录；`--scope global` 可把版本偏好或映射存为个人全局配置。

## 验证

全部 `SKILL.md` 通过 skill-creator 的 `quick_validate.py` 校验；四个脚本均用合成 MFC 样例实测通过。
