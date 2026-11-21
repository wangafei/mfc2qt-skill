#!/usr/bin/env python3
"""Extract dialog/control inventory from an MFC .rc file.

Parses DIALOG/DIALOGEX blocks and their controls, plus top-level MENU,
ACCELTABLE, STRINGTABLE and other resource declarations. Output is a lead
list: verify against resource.h and the real dialog before generating .ui.

Handles the real MFC CONTROL grammar:
    CONTROL caption, id, "class", style, x, y, width, height [, exstyle]
and keyword forms:
    EDITTEXT id, x, y, width, height [, style]
"""
import argparse
import json
import re
import sys

DIALOG_RE = re.compile(
    r"^\s*(\w+)\s+(DIALOGEX?|DIALOG)\s+"
    r"([-\d]+)\s*,\s*([-\d]+)\s*,\s*([-\d]+)\s*,\s*([-\d]+)",
    re.IGNORECASE,
)
OTHER_RE = re.compile(r"^\s*(\w+)\s+(MENU|ACCELTABLE|STRINGTABLE|ICON|BITMAP|TOOLBAR)\b", re.IGNORECASE)
KEYWORD_KINDS = {"EDITTEXT", "BUTTON", "STATIC", "COMBOBOX", "LISTBOX", "SCROLLBAR",
                 "LTEXT", "CTEXT", "RTEXT", "AUTOCHECKBOX", "AUTORADIOBUTTON",
                 "PUSHBUTTON", "DEFPUSHBUTTON", "CHECKBOX", "RADIOBUTTON", "GROUPBOX"}

STYLE_HINTS = {
    "BS_DEFPUSHBUTTON": "QPushButton (default)", "BS_PUSHBUTTON": "QPushButton",
    "BS_AUTOCHECKBOX": "QCheckBox", "BS_CHECKBOX": "QCheckBox",
    "BS_AUTORADIOBUTTON": "QRadioButton", "BS_RADIOBUTTON": "QRadioButton",
    "BS_GROUPBOX": "QGroupBox", "BS_OWNERDRAW": "QToolButton / custom",
    "BS_BITMAP": "QToolButton / QPushButton with icon",
    "ES_MULTILINE": "QTextEdit", "ES_PASSWORD": "QLineEdit (Password)",
    "ES_READONLY": "QLineEdit (readOnly)", "ES_NUMBER": "QLineEdit + QIntValidator",
    "CBS_DROPDOWNLIST": "QComboBox", "LBS_EXTENDEDSEL": "QListWidget (ExtendedSelection)",
}


def split_commas(line):
    """Split a resource line on commas that are outside double quotes."""
    tokens, buf, in_quotes = [], [], False
    for ch in line:
        if ch == '"':
            in_quotes = not in_quotes
            buf.append(ch)
        elif ch == ',' and not in_quotes:
            tokens.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf).strip())
    return tokens


def unquote(text):
    return text.strip().strip('"')


def guess_widget(kind, class_name, style):
    kind = (kind or "").upper()
    hay = "%s %s" % (kind, style)
    if kind in ("EDITTEXT",):
        if "ES_MULTILINE" in style:
            return "QTextEdit"
        return "QLineEdit"
    if kind in ("LTEXT", "CTEXT", "RTEXT", "STATIC"):
        return "QLabel"
    if kind in ("PUSHBUTTON", "DEFPUSHBUTTON"):
        return "QPushButton"
    if kind in ("AUTOCHECKBOX", "CHECKBOX"):
        return "QCheckBox"
    if kind in ("AUTORADIOBUTTON", "RADIOBUTTON"):
        return "QRadioButton"
    if kind == "GROUPBOX":
        return "QGroupBox"
    if kind == "BUTTON":
        for token, widget in STYLE_HINTS.items():
            if token.startswith("BS_") and token in style:
                return widget
        return "QPushButton"
    if kind == "COMBOBOX":
        return "QComboBox"
    if kind == "LISTBOX":
        return "QListWidget"
    if kind == "SCROLLBAR":
        return "QScrollBar"
    cls = (class_name or "").lower()
    if "listview" in cls:
        return "QTableView / QTreeWidget"
    if "treeview" in cls:
        return "QTreeView / QTreeWidget"
    if "progress" in cls:
        return "QProgressBar"
    if "trackbar" in cls:
        return "QSlider"
    if "datetime" in cls:
        return "QDateTimeEdit"
    if "button" in cls:
        return "QPushButton"
    if "static" in cls:
        return "QLabel"
    return "QWidget (custom/promoted)"


def parse_control(line):
    tokens = split_commas(line.strip())
    if len(tokens) < 5:
        return None
    head = tokens[0].split(None, 1)
    kind = head[0].upper() if head else ""
    if kind == "CONTROL":
        if len(tokens) < 8:
            return None
        text = unquote(tokens[0][len("CONTROL"):].strip())
        ctrl_id = unquote(tokens[1])
        class_name = unquote(tokens[2])
        style = tokens[3]
        coords = tokens[4:8]
    elif kind in KEYWORD_KINDS:
        # LTEXT/CTEXT/RTEXT carry caption first, then ID, then coords.
        # Other keyword forms start with the ID directly.
        if kind in ("LTEXT", "CTEXT", "RTEXT"):
            text = unquote(head[1]) if len(head) > 1 else ""
            ctrl_id = unquote(tokens[1])
            coords = tokens[2:6]
            style = ""
        else:
            text = ""
            ctrl_id = unquote(head[1]) if len(head) > 1 else ""
            style = tokens[-1] if len(tokens) >= 6 else ""
            coords = tokens[1:5]
        class_name = ""
    else:
        return None
    try:
        rect = [int(v) for v in coords]
    except ValueError:
        return None
    if len(rect) != 4:
        return None
    return {
        "id": ctrl_id, "kind": class_name if kind == "CONTROL" else kind,
        "text": text, "rect": rect, "style": style,
        "suggested_widget": guess_widget(kind, class_name, style),
    }


def parse(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        lines = fh.readlines()
    result = {"dialogs": [], "other_resources": []}
    current = None
    for lineno, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        if current is None:
            m = DIALOG_RE.match(line)
            if m:
                current = {
                    "id": m.group(1), "type": m.group(2).upper(),
                    "rect": [int(m.group(i)) for i in range(3, 7)],
                    "line": lineno, "controls": [],
                }
                result["dialogs"].append(current)
                continue
            o = OTHER_RE.match(line)
            if o:
                result["other_resources"].append(
                    {"id": o.group(1), "type": o.group(2).upper(), "line": lineno})
            continue
        ctrl = parse_control(line)
        if ctrl:
            ctrl["line"] = lineno
            current["controls"].append(ctrl)
        if re.search(r"^\s*END\s*$", line, re.IGNORECASE):
            current = None
    return result


def render_markdown(data, path):
    out = ["# .rc Resource Inventory", "", "File: `%s`" % path, ""]
    out += ["## Dialogs (%d)" % len(data["dialogs"]), ""]
    for dlg in data["dialogs"]:
        out += ["### %s (%s) — line %d" % (dlg["id"], dlg["type"], dlg["line"]), ""]
        out += ["Rect (DLU): %s" % dlg["rect"], ""]
        if not dlg["controls"]:
            out += ["_No controls parsed; check for nested/complex syntax._", ""]
            continue
        out += ["| ID | .rc kind | Suggested Qt widget | Text | Rect |", "|---|---|---|---|---|"]
        for c in dlg["controls"]:
            text = c["text"].replace("|", "\\|")
            out.append("| %s | %s | %s | %s | %s |" % (
                c["id"], c["kind"], c["suggested_widget"], text, c["rect"]))
        out.append("")
    out += ["## Other Resources", ""]
    if data["other_resources"]:
        out += ["| ID | Type | Line |", "|---|---|---|"]
        for r in data["other_resources"]:
            out.append("| %s | %s | %d |" % (r["id"], r["type"], r["line"]))
    else:
        out.append("_None detected._")
    out += ["", "> Leads only. Confirm styles against resource.h and the real dialog."]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rc_file", help="path to the MFC .rc file")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    try:
        data = parse(args.rc_file)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.json
          else render_markdown(data, args.rc_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
