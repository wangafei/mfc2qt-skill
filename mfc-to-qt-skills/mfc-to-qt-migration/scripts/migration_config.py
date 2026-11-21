#!/usr/bin/env python3
"""MFC→Qt migration project configuration.

Manages two things that must survive across sessions and across skills:

  * Qt version selection: auto-detect or user-specified (Qt 5 / Qt 6 / exact).
  * User-defined MFC control -> Qt widget mappings (with disk persistence).

Project config : <project-root>/.mfc-qt/config.json
Global config  : ~/.mfc-to-qt-skills/config.json   (--scope global)

Project values override global values field by field. Built-in defaults are
used only when neither config defines a mapping.

Stdlib only. Examples:

    python migration_config.py init --root D:/work/myapp
    python migration_config.py set-qt auto --root D:/work/myapp
    python migration_config.py set-qt 5.15 --root D:/work/myapp
    python migration_config.py detect --root D:/work/myapp
    python migration_config.py map list --root D:/work/myapp
    python migration_config.py map add MyGridCtrl QTableView --header QtWidgets/QTableView
    python migration_config.py map remove MyGridCtrl --root D:/work/myapp
    python migration_config.py map import mappings.json --root D:/work/myapp
    python migration_config.py show --root D:/work/myapp --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1
PROJECT_RELATIVE = Path(".mfc-qt") / "config.json"
GLOBAL_RELATIVE = Path(".mfc-to-qt-skills") / "config.json"


# Built-in fallback table. Keys are normalized (lowercase, alnum only).
BUILTIN_MAP = {
    "edittext": {"widget": "QLineEdit", "source": "builtin"},
    "edittext_multiline": {"widget": "QTextEdit", "source": "builtin"},
    "button": {"widget": "QPushButton", "source": "builtin"},
    "button_check": {"widget": "QCheckBox", "source": "builtin"},
    "button_radio": {"widget": "QRadioButton", "source": "builtin"},
    "button_group": {"widget": "QGroupBox", "source": "builtin"},
    "combobox": {"widget": "QComboBox", "source": "builtin"},
    "listbox": {"widget": "QListWidget", "source": "builtin"},
    "scrollbar": {"widget": "QScrollBar", "source": "builtin"},
    "static": {"widget": "QLabel", "source": "builtin"},
    "ctl_syslistview32": {"widget": "QTableView", "source": "builtin"},
    "ctl_systreeview32": {"widget": "QTreeView", "source": "builtin"},
    "ctl_msctls_progress32": {"widget": "QProgressBar", "source": "builtin"},
    "ctl_msctls_trackbar32": {"widget": "QSlider", "source": "builtin"},
    "ctl_sysdatetimepick32": {"widget": "QDateTimeEdit", "source": "builtin"},
    "ctl_msctls_updown32": {"widget": "QSpinBox", "source": "builtin"},
}

EMPTY_CONFIG = {
    "schemaVersion": SCHEMA_VERSION,
    "qt": {"requested": "auto", "resolvedMajor": None, "minVersion": "", "components": ["Widgets"]},
    "controlMap": {},
}


def normalize_token(token: str) -> str:
    """IDC_FOO, 'SysListView32' and 'CMyCtrl' -> stable lookup key."""
    t = token.strip().lower()
    t = re.sub(r"^idc_", "", t)
    t = re.sub(r"^ctl_", "ctl_", t)
    return re.sub(r"[^a-z0-9_]", "", t)


def project_config_path(root: Path) -> Path:
    return root / PROJECT_RELATIVE


def global_config_path() -> Path:
    return Path.home() / GLOBAL_RELATIVE


def config_path(root: Path, scope: str) -> Path:
    return global_config_path() if scope == "global" else project_config_path(root)


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return {}
    return data if isinstance(data, dict) else {}


def save_config(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data["schemaVersion"] = SCHEMA_VERSION
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"saved: {path}")


def merged_config(root: Path) -> dict:
    """Merge global <- project, field by field."""
    out = json.loads(json.dumps(EMPTY_CONFIG))
    for layer in (load_config(global_config_path()), load_config(project_config_path(root))):
        if not layer:
            continue
        for key in ("qt", "controlMap"):
            value = layer.get(key)
            if isinstance(value, dict):
                out[key].update(value)
    return out


def effective_map(root: Path) -> dict:
    result = {k: dict(v) for k, v in BUILTIN_MAP.items()}
    for key, value in merged_config(root)["controlMap"].items():
        if isinstance(value, str):
            value = {"widget": value}
        if not isinstance(value, dict) or not value.get("widget"):
            continue
        entry = dict(value)
        entry.setdefault("source", "user")
        result[normalize_token(key)] = entry
    return result


def detect_qt(root: Path) -> dict:
    """Read-only detection. Returns evidence list and a suggested major."""
    evidence = []
    cmake_files = []
    for candidate in (root / "CMakeLists.txt", root / "CMakeLists.txt.in"):
        if candidate.exists():
            cmake_files.append(candidate)
    try:
        cmake_files.extend(sorted(root.glob("*/CMakeLists.txt"))[:30])
    except OSError:
        pass

    text = ""
    for cf in cmake_files:
        try:
            text += cf.read_text(encoding="utf-8", errors="ignore") + "\n"
        except OSError:
            pass
    for major in ("6", "5"):
        if re.search(r"find_package\s*\(\s*Qt" + major + r"\b", text, re.IGNORECASE):
            evidence.append(f"CMakeLists.txt: find_package(Qt{major} ...)")
    for env_name in ("QT_VERSION", "QT_ROOT", "QT_DIR", "Qt6_DIR", "Qt5_DIR"):
        value = os.environ.get(env_name)
        if value:
            evidence.append(f"env {env_name}={value}")

    for exe in ("qmake6", "qmake-qt5", "qmake"):
        found = shutil.which(exe)
        if not found:
            continue
        try:
            proc = subprocess.run([found, "-v"], capture_output=True, text=True, timeout=5)
            out = (proc.stdout + proc.stderr).strip().splitlines()
            line = out[0] if out else ""
        except (OSError, subprocess.SubprocessError):
            line = ""
        version = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", line)
        if version:
            major = version.group(1)
            evidence.append(f"{exe}: Qt {version.group(0)}")
            if major not in ("5", "6"):
                major = ""
            if major:
                return {"evidence": evidence, "suggestedMajor": major,
                        "suggestedVersion": version.group(0)}

    majors = {re.search(r"Qt([56])", e).group(1) for e in evidence if re.search(r"Qt([56])", e)}
    suggested = next(iter(majors)) if len(majors) == 1 else ""
    return {"evidence": evidence, "suggestedMajor": suggested, "suggestedVersion": ""}


def parse_requested(value: str) -> dict:
    v = value.strip().lower()
    if v in ("auto", "", "detect"):
        return {"requested": "auto", "resolvedMajor": None, "minVersion": ""}
    m = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", v)
    if not m:
        raise ValueError(f"unsupported Qt version: {value!r}; use auto|5|6|5.15|6.5.3")
    major = m.group(1)
    if major not in ("5", "6"):
        raise ValueError(f"only Qt 5 and Qt 6 are supported, got major {major}")
    digits = [g for g in m.groups()[1:] if g]
    return {
        "requested": value.strip(),
        "resolvedMajor": major,
        "minVersion": ".".join([major] + digits) if digits else "",
    }


def fmt_map(entries: dict) -> str:
    lines = ["| MFC 标记 | Qt widget | 来源 | 备注 |", "|---|---|---|---|"]
    for key in sorted(entries):
        item = entries[key]
        note = item.get("note", "")
        header = item.get("header", "")
        if header and note:
            note = f"{note} ({header})"
        elif header:
            note = header
        lines.append(f"| `{key}` | `{item['widget']}` | {item.get('source', '')} | {note} |")
    return "\n".join(lines)


def cmd_init(args):
    path = config_path(args.root, args.scope)
    if path.exists() and not args.force:
        print(f"already exists (use --force to reset): {path}")
        return
    save_config(path, json.loads(json.dumps(EMPTY_CONFIG)))
    print("Next: set-qt auto|5|6|5.15, or map add <MFC token> <Qt widget>")


def cmd_show(args):
    cfg = merged_config(args.root)
    if args.detect:
        cfg["detection"] = detect_qt(args.root)
    if args.json:
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return
    qt = cfg["qt"]
    print(f"project root : {args.root}")
    print(f"project cfg  : {project_config_path(args.root)}")
    print(f"global cfg   : {global_config_path()}")
    print(f"qt.requested : {qt.get('requested', 'auto')}")
    print(f"qt.major     : {qt.get('resolvedMajor') or '(unresolved)'}")
    print(f"qt.minVersion: {qt.get('minVersion') or '-'}")
    print(f"user mappings: {len(cfg['controlMap'])}")
    if args.detect:
        d = cfg["detection"]
        print(f"detected     : major={d['suggestedMajor'] or 'ambiguous'}")
        for item in d["evidence"]:
            print(f"  - {item}")
    if cfg["controlMap"]:
        print()
        print(fmt_map(effective_map(args.root)))


def cmd_detect(args):
    result = detect_qt(args.root)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print(f"suggested Qt major: {result['suggestedMajor'] or 'ambiguous (ask the user)'}")
    for item in result["evidence"]:
        print(f"  - {item}")
    if not result["evidence"]:
        print("  (no CMakeLists.txt / qmake / Qt env found)")


def cmd_set_qt(args):
    parsed = parse_requested(args.version)
    path = config_path(args.root, args.scope)
    cfg = load_config(path) or json.loads(json.dumps(EMPTY_CONFIG))
    cfg.setdefault("qt", {})
    cfg["qt"].update(parsed)
    save_config(path, cfg)
    if parsed["resolvedMajor"]:
        print(f"Qt {parsed['resolvedMajor']} selected (minVersion={parsed['minVersion'] or '-'})")
    else:
        print("Qt version = auto; run 'detect' before generating CMake/code.")


def cmd_map_list(args):
    entries = effective_map(args.root)
    if args.json:
        print(json.dumps(entries, indent=2, ensure_ascii=False))
        return
    print(fmt_map(entries))
    print(f"\n{len(entries)} effective mappings (built-in + user overrides).")


def cmd_map_add(args):
    path = config_path(args.root, args.scope)
    cfg = load_config(path) or json.loads(json.dumps(EMPTY_CONFIG))
    cfg.setdefault("controlMap", {})
    key = normalize_token(args.token)
    entry = {"widget": args.widget}
    if args.header:
        entry["header"] = args.header
    if args.note:
        entry["note"] = args.note
    if args.source:
        entry["source"] = args.source
    if key in cfg["controlMap"] and not args.force:
        print(f"mapping exists (use --force to overwrite): {key}")
        return
    cfg["controlMap"][key] = entry
    save_config(path, cfg)
    print(f"mapping: {key} -> {args.widget}")


def cmd_map_remove(args):
    path = config_path(args.root, args.scope)
    cfg = load_config(path)
    key = normalize_token(args.token)
    if key not in cfg.get("controlMap", {}):
        print(f"not found in {path}: {key}")
        return
    del cfg["controlMap"][key]
    save_config(path, cfg)
    print(f"removed: {key}")


def cmd_map_import(args):
    incoming = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if isinstance(incoming, dict) and "controlMap" in incoming:
        incoming = incoming["controlMap"]
    if not isinstance(incoming, dict):
        raise ValueError("import file must be a JSON object of token -> widget/entry")
    path = config_path(args.root, args.scope)
    cfg = load_config(path) or json.loads(json.dumps(EMPTY_CONFIG))
    cfg.setdefault("controlMap", {})
    added = 0
    for token, value in incoming.items():
        if isinstance(value, str):
            value = {"widget": value}
        if not isinstance(value, dict) or not value.get("widget"):
            continue
        cfg["controlMap"][normalize_token(token)] = value
        added += 1
    save_config(path, cfg)
    print(f"imported {added} mapping(s)")


def cmd_map_export(args):
    entries = {k: v for k, v in effective_map(args.root).items()
               if v.get("source") == "user"}
    if args.format == "json":
        print(json.dumps(entries, indent=2, ensure_ascii=False))
    else:
        print(fmt_map(entries))


def cmd_where(args):
    print(f"project: {project_config_path(args.root)}")
    print(f"global : {global_config_path()}")
    print(f"active : {config_path(args.root, args.scope)}")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=None, help="MFC project root (default: cwd)")
    common.add_argument("--scope", choices=["project", "global"], default="project",
                        help="which config file to write (default: project)")

    sub = p.add_subparsers(dest="command", required=True)

    ini = sub.add_parser("init", parents=[common], help="create a config file")
    ini.add_argument("--force", action="store_true")
    ini.set_defaults(func=cmd_init)

    show = sub.add_parser("show", parents=[common], help="show effective configuration")
    show.add_argument("--json", action="store_true")
    show.add_argument("--detect", action="store_true")
    show.set_defaults(func=cmd_show)

    det = sub.add_parser("detect", parents=[common], help="read-only Qt version detection")
    det.add_argument("--json", action="store_true")
    det.set_defaults(func=cmd_detect)

    setq = sub.add_parser("set-qt", parents=[common], help="set Qt version: auto|5|6|5.15|6.5")
    setq.add_argument("version")
    setq.set_defaults(func=cmd_set_qt)

    mp = sub.add_parser("map", parents=[common], help="control mapping management")
    msub = mp.add_subparsers(dest="map_command", required=True)

    ml = msub.add_parser("list", parents=[common])
    ml.add_argument("--json", action="store_true")
    ml.set_defaults(func=cmd_map_list)

    ma = msub.add_parser("add", parents=[common])
    ma.add_argument("token", help="MFC class / window class / IDC token")
    ma.add_argument("widget", help="Qt widget class, e.g. QTableView")
    ma.add_argument("--header", help="include path, e.g. QtWidgets/QTableView")
    ma.add_argument("--note")
    ma.add_argument("--source", default="user")
    ma.add_argument("--force", action="store_true")
    ma.set_defaults(func=cmd_map_add)

    mr = msub.add_parser("remove", parents=[common])
    mr.add_argument("token")
    mr.set_defaults(func=cmd_map_remove)

    mi = msub.add_parser("import", parents=[common])
    mi.add_argument("file", type=Path)
    mi.set_defaults(func=cmd_map_import)

    me = msub.add_parser("export", parents=[common])
    me.add_argument("--format", choices=["json", "md"], default="md")
    me.set_defaults(func=cmd_map_export)

    wh = sub.add_parser("where", parents=[common])
    wh.set_defaults(func=cmd_where)
    return p


def main():
    args = build_parser().parse_args()
    args.root = (args.root or Path.cwd()).expanduser().resolve()
    try:
        args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
