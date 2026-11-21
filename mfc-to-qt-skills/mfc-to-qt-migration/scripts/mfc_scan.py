#!/usr/bin/env python3
"""Scan an MFC project for migration-relevant patterns.

Produces a Markdown or JSON lead report. Output is a lead generator only:
always confirm findings by reading the source files.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

PATTERNS = {
    "resource": [
        (r"\b(DIALOGEX?|MENU|ACCELTABLE|STRINGTABLE|ICON|BITMAP|TOOLBAR)\b", ".rc resource block"),
    ],
    "message_map": [
        (r"\bBEGIN_MESSAGE_MAP\b", "message map begin"),
        (r"\bON_BN_CLICKED\b", "button click macro"),
        (r"\bON_COMMAND(_RANGE)?\b", "command macro"),
        (r"\bON_UPDATE_COMMAND_UI\b", "UI update macro"),
        (r"\bON_NOTIFY\b", "notify macro"),
        (r"\bON_CBN_\w+\b", "combo-box notification macro"),
        (r"\bON_EN_\w+\b", "edit notification macro"),
        (r"\bON_LBN_\w+\b", "list-box notification macro"),
        (r"\bON_WM_\w+\b", "WM_ handler macro"),
        (r"\bON_MESSAGE\b", "custom message macro"),
    ],
    "binding": [
        (r"\bDDX_\w+\s*\(", "DDX macro"),
        (r"\bDDV_\w+\s*\(", "DDV macro"),
        (r"\bUpdateData\s*\(", "UpdateData call"),
        (r"\bDoDataExchange\b", "DoDataExchange override"),
    ],
    "layout_geometry": [
        (r"\bOnSize\s*\(", "OnSize handler"),
        (r"\bMoveWindow\s*\(", "MoveWindow call"),
        (r"\bSetWindowPos\s*\(", "SetWindowPos call"),
        (r"\bGetWindowRect\s*\(", "GetWindowRect call"),
        (r"\bGetClientRect\s*\(", "GetClientRect call"),
        (r"\bCenterWindow\s*\(", "CenterWindow call"),
        (r"\bScreenToClient\s*\(", "ScreenToClient call"),
        (r"\bClientToScreen\s*\(", "ClientToScreen call"),
    ],
    "dialogs": [
        (r"\.DoModal\s*\(", "DoModal call"),
        (r"\bDoModal\s*\(\s*\)", "DoModal declaration/call"),
        (r"\bEndDialog\s*\(", "EndDialog call"),
        (r"\bOnInitDialog\b", "OnInitDialog override"),
    ],
    "input": [
        (r"\bPreTranslateMessage\b", "PreTranslateMessage override"),
        (r"\bOnKeyDown\b|\bOnChar\b|\bOnKeyUp\b", "keyboard handler"),
        (r"\bOnLButton(Down|Up|DblClk)\b|\bOnMouseMove\b", "mouse handler"),
        (r"\bGetKeyState\s*\(", "key-state query"),
        (r"\bSetCapture\s*\(", "mouse capture"),
    ],
    "messaging": [
        (r"\bSendMessage\s*\(", "SendMessage call"),
        (r"\bPostMessage\s*\(", "PostMessage call"),
        (r"\bRegisterWindowMessage\s*\(", "registered message"),
        (r"\bWM_USER\b", "WM_USER range"),
    ],
    "mfc_core": [
        (r"#\s*include\s*[<\"](afxwin|afxdlgs|afxext|afxcmn)\.h", "MFC core include"),
        (r"\btheApp\b|\bAfxGetApp\b|\bAfxMessageBox\b", "MFC global API"),
    ],
}

SCAN_EXTS = {".h", ".hpp", ".cpp", ".cc", ".cxx", ".rc", ".idl"}
SKIP_DIRS = {".git", ".svn", "build", "Debug", "Release", "x64", "ipch", ".vs"}


def compile_patterns():
    return {cat: [(re.compile(p), d) for p, d in items] for cat, items in PATTERNS.items()}


def scan(root, compiled):
    findings = defaultdict(lambda: defaultdict(list))
    files_scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if os.path.splitext(name)[1].lower() not in SCAN_EXTS:
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            files_scanned += 1
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, 1):
                for cat, items in compiled.items():
                    for rx, desc in items:
                        if rx.search(line):
                            findings[cat][desc].append({"file": rel, "line": lineno})
    return findings, files_scanned


def render_markdown(findings, files_scanned, root):
    out = ["# MFC Migration Scan Report", "", "Root: `%s`" % root,
           "Files scanned: %d" % files_scanned, ""]
    total = 0
    for cat in PATTERNS:
        buckets = findings.get(cat)
        if not buckets:
            continue
        cat_total = sum(len(v) for v in buckets.values())
        total += cat_total
        out += ["## %s (%d)" % (cat, cat_total), ""]
        out += ["| Pattern | Count | Locations |", "|---|---:|---|"]
        for desc, hits in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
            locs = ", ".join("`%s:%d`" % (h["file"], h["line"]) for h in hits[:8])
            if len(hits) > 8:
                locs += " (+%d more)" % (len(hits) - 8)
            out.append("| %s | %d | %s |" % (desc, len(hits), locs))
        out.append("")
    out += ["## Total", "", "Matches: %d" % total, "",
            "> Treat these as leads. Confirm each finding in source before migrating."]
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="MFC project root directory")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args()
    if not os.path.isdir(args.root):
        print("Not a directory: %s" % args.root, file=sys.stderr)
        return 2
    compiled = compile_patterns()
    findings, files_scanned = scan(args.root, compiled)
    if args.json:
        payload = {
            "root": os.path.abspath(args.root),
            "files_scanned": files_scanned,
            "findings": {cat: dict(buckets) for cat, buckets in findings.items()},
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(findings, files_scanned, os.path.abspath(args.root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
