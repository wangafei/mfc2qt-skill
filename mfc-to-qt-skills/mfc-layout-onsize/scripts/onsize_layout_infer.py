#!/usr/bin/env python3
"""Infer Qt layout structure from MFC OnSize geometry code.

Reads C++ source, finds OnSize-like handlers, parses MoveWindow/SetWindowPos
coordinate expressions as linear functions of cx/cy, groups adjacent controls
into horizontal/vertical chains, and emits a suggested Qt layout tree plus a
.ui XML fragment.

Stdlib only. Examples:

    python onsize_layout_infer.py MyDlg.cpp
    python onsize_layout_infer.py MyDlg.cpp MyView.cpp --root D:/work/app
    python onsize_layout_infer.py MyDlg.cpp --json
    python onsize_layout_infer.py MyDlg.cpp --ui-out suggestion.ui.xml

Output is a *suggestion*: confirm control semantics before applying it.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

TOL = Fraction(1, 1000)
ZERO = Fraction(0)
ONE = Fraction(1)


# --------------------------------------------------------------------------
# Linear expressions: a*cx + b*cy + c
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Lin:
    cx: Fraction = ZERO
    cy: Fraction = ZERO
    c: Fraction = ZERO

    def __add__(self, other):
        return Lin(self.cx + other.cx, self.cy + other.cy, self.c + other.c)

    def __sub__(self, other):
        return Lin(self.cx - other.cx, self.cy - other.cy, self.c - other.c)

    def __mul__(self, other):
        if isinstance(other, Lin):
            s = scalar(other)
            if s is None:
                return None
            other = s
        return Lin(self.cx * other, self.cy * other, self.c * other)

    def __truediv__(self, other):
        if isinstance(other, Lin):
            other = scalar(other)
        if other is None or other == 0:
            return None
        return Lin(self.cx / other, self.cy / other, self.c / other)

    def __neg__(self):
        return Lin(-self.cx, -self.cy, -self.c)


def scalar(v: Lin):
    if abs(v.cx) <= TOL and abs(v.cy) <= TOL:
        return v.c
    return None


def near_zero(v: Lin) -> bool:
    return abs(v.cx) <= TOL and abs(v.cy) <= TOL and abs(v.c) <= TOL


def close(a, b) -> bool:
    return a is not None and b is not None and near_zero(a - b)


def fmt(v) -> str:
    if v is None:
        return "?"
    parts = []
    for coef, sym in ((v.cx, "cx"), (v.cy, "cy")):
        if abs(coef) <= TOL:
            continue
        if abs(coef - ONE) <= TOL:
            parts.append(sym)
        elif abs(coef + ONE) <= TOL:
            parts.append(f"-{sym}")
        else:
            parts.append(f"{float(coef):g}*{sym}")
    if abs(v.c) > TOL:
        if v.c < 0:
            sign = "-"
        elif parts:
            sign = "+"
        else:
            sign = ""
        parts.append(f"{sign}{abs(float(v.c)):g}")
    return " ".join(parts) if parts else "0"


BASIS = {
    "cx": Lin(ONE), "cy": Lin(0, ONE),
    "nwidth": Lin(ONE), "nheight": Lin(0, ONE),
    "width": Lin(ONE), "height": Lin(0, ONE),
    "nwidth_": Lin(ONE), "nheight_": Lin(0, ONE),
}


def sanitize(expr: str) -> str:
    e = expr.strip()
    e = re.sub(r"/\*.*?\*/", " ", e)
    e = re.sub(r"//.*$", " ", e)
    e = e.replace("TRUE", "1").replace("FALSE", "0")
    e = e.replace("true", "1").replace("false", "0")
    e = e.replace("nullptr", "0").replace("NULL", "0")
    e = re.sub(r"\b[A-Za-z_]\w*\.Width\(\)", "cx", e)
    e = re.sub(r"\b[A-Za-z_]\w*\.Height\(\)", "cy", e)
    e = re.sub(r"\b[A-Za-z_]\w*\.right\b", "cx", e)
    e = re.sub(r"\b[A-Za-z_]\w*\.bottom\b", "cy", e)
    e = re.sub(r"\b[A-Za-z_]\w*\.left\b", "0", e)
    e = re.sub(r"\b[A-Za-z_]\w*\.top\b", "0", e)
    e = re.sub(r"\(\s*(?:int|UINT|LONG|long|short|float|double|BOOL)\s*\)", "", e)
    return e.strip()


def eval_expr(expr: str, symbols: dict) -> Lin | None:
    e = sanitize(expr)
    if not e or any(tok in e for tok in ("?", "&&", "||", "<<", ">>")):
        return None
    try:
        tree = ast.parse(e, mode="eval")
    except SyntaxError:
        return None

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return Lin(c=ONE if node.value else ZERO)
            if isinstance(node.value, (int, float)):
                return Lin(c=Fraction(str(node.value)))
            return None
        if isinstance(node, ast.Name):
            key = node.id.lower()
            if node.id in symbols:
                return symbols[node.id]
            return BASIS.get(key)
        if isinstance(node, ast.UnaryOp):
            v = visit(node.operand)
            if v is None:
                return None
            if isinstance(node.op, ast.USub):
                return -v
            if isinstance(node.op, ast.UAdd):
                return v
            return None
        if isinstance(node, ast.BinOp):
            a, b = visit(node.left), visit(node.right)
            if a is None or b is None:
                return None
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            if isinstance(node.op, ast.Mult):
                result = a * b
                return result if isinstance(result, Lin) else None
            if isinstance(node.op, (ast.Div, ast.FloorDiv)):
                result = a / b
                return result if isinstance(result, Lin) else None
            return None
        return None

    try:
        return visit(tree)
    except (ValueError, ZeroDivisionError, TypeError):
        return None


# --------------------------------------------------------------------------
# C++ source helpers
# --------------------------------------------------------------------------
def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return text


def match_delim(text: str, start: int, opening: str, closing: str) -> int:
    depth, i = 0, start
    in_str = None
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in ('"', "'"):
                in_str = ch
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def split_args(content: str) -> list[str]:
    out, start, depth, in_str = [], 0, 0, None
    i = 0
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == in_str:
                in_str = None
        elif ch in ('"', "'"):
            in_str = ch
        elif ch in "(<[":
            depth += 1
        elif ch in ")>]":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            out.append(content[start:i].strip())
            start = i + 1
        i += 1
    out.append(content[start:].strip())
    return [a for a in out if a]


HANDLER_RE = re.compile(
    r"\b(?:afx_msg\s+)?(?:void|BOOL|int|LRESULT)\s+"
    r"(?:[A-Za-z_]\w*\s*::\s*)?(OnSize|OnResize|OnSizeChanged|OnWindowPosChanged)\s*"
    r"\([^;{}]*\)\s*\{"
)


def find_bodies(text: str) -> list[tuple[str, str]]:
    """Return (handler name or '<block>', body) pairs, without handler duplicates."""
    bodies = []
    handler_spans = []
    for m in HANDLER_RE.finditer(text):
        brace = m.end() - 1
        end = match_delim(text, brace, "{", "}")
        if end > 0:
            bodies.append((m.group(1), text[brace + 1:end]))
            handler_spans.append((brace, end))
    for m in re.finditer(r"\{", text):
        brace, end = m.start(), match_delim(text, m.start(), "{", "}")
        if end < 0:
            continue
        # Skip the handler bodies themselves and any enclosing block (class/function)
        # that merely contains them.
        if any(hb <= brace and end <= he for hb, he in handler_spans):
            continue
        body = text[brace + 1:end]
        if body.count("MoveWindow(") + body.count("SetWindowPos(") >= 2:
            bodies.append(("<block>", body))
    return bodies


def local_symbols(body: str) -> dict:
    symbols: dict = {}
    pattern = re.compile(
        r"\b(?:int|UINT|LONG|long|short|float|double|BOOL|size_t|auto)\s+"
        r"([A-Za-z_]\w*)\s*=\s*([^;]+);"
    )
    for _ in range(4):
        changed = False
        for m in pattern.finditer(body):
            name, expr = m.group(1), m.group(2)
            value = eval_expr(expr, symbols)
            if value is not None and (name not in symbols or not close(symbols[name], value)):
                symbols[name] = value
                changed = True
        if not changed:
            break
    return symbols


@dataclass
class Call:
    func: str
    target: str
    x: Lin | None
    y: Lin | None
    w: Lin | None
    h: Lin | None
    raw: str

    @property
    def ok(self) -> bool:
        return all(v is not None for v in (self.x, self.y, self.w, self.h))

    @property
    def mfc_id(self) -> str:
        m = re.search(r"IDC_[A-Za-z0-9_]+", self.target)
        return m.group(0) if m else ""


def parse_calls(body: str, symbols: dict) -> list[Call]:
    calls = []
    for m in re.finditer(r"\b(MoveWindow|SetWindowPos)\s*\(", body):
        func = m.group(1)
        op = m.end() - 1
        end = match_delim(body, op, "(", ")")
        if end < 0:
            continue
        args = split_args(body[op + 1:end])
        prefix = body[:m.start()]
        target_match = re.search(r"([A-Za-z_]\w*|IDC_[A-Za-z0-9_]+)\s*(?:\.|->)\s*$", prefix)
        target = target_match.group(1) if target_match else ""

        geo = []
        if func == "MoveWindow":
            if len(args) >= 5:
                geo = args[1:5]
            elif len(args) >= 4:
                geo = args[:4]
        else:
            if len(args) >= 7:
                geo = args[2:6]
            elif len(args) >= 6:
                geo = args[1:5]
        if len(geo) != 4:
            continue
        if not target and args and func == "MoveWindow":
            target = re.sub(r"\W+", "_", args[0])[:40]
        vals = [eval_expr(a, symbols) for a in geo]
        raw = body[m.start():end + 1].replace("\n", " ")
        calls.append(Call(func, target or "<unknown>", *vals, raw=raw))
    return calls


# --------------------------------------------------------------------------
# Layout tree inference
# --------------------------------------------------------------------------
@dataclass
class Node:
    name: str
    x: Lin
    y: Lin
    w: Lin
    h: Lin
    orient: str = ""
    children: list = field(default_factory=list)
    mfc_id: str = ""

    def is_leaf(self) -> bool:
        return not self.children


def make_node(call: Call) -> Node:
    safe = [v if v is not None else Lin() for v in (call.x, call.y, call.w, call.h)]
    return Node(call.target, *safe, mfc_id=call.mfc_id)


def chain_clusters(nodes: list[Node], orient: str) -> list[list[Node]]:
    """Group nodes into maximal chains along one axis."""
    if orient == "H":
        axis_start, axis_len, cross_a, cross_b = "x", "w", "y", "h"
    else:
        axis_start, axis_len, cross_a, cross_b = "y", "h", "x", "w"

    def start_of(n):
        return getattr(n, axis_start)

    def span(n):
        return getattr(n, axis_len)

    ordered = sorted(nodes, key=lambda n: (float(start_of(n).cx), float(start_of(n).cy), float(start_of(n).c)))

    parent = list(range(len(ordered)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            a, b = ordered[i], ordered[j]
            if not close(getattr(a, cross_a), getattr(b, cross_a)):
                continue
            if not close(getattr(a, cross_b), getattr(b, cross_b)):
                continue
            gap = start_of(b) - (start_of(a) + span(a))
            s = scalar(gap)
            if s is None or s < -TOL:
                continue
            union(i, j)

    groups: dict = {}
    for i, n in enumerate(ordered):
        groups.setdefault(find(i), []).append(n)
    return [g for g in groups.values() if len(g) >= 2]


def merge_group(group: list[Node], orient: str) -> Node:
    xs = [n.x for n in group]
    ys = [n.y for n in group]
    rights = [n.x + n.w for n in group]
    bottoms = [n.y + n.h for n in group]
    ordered = sorted(group, key=lambda n: (float(n.x.cx), float(n.x.cy), float(n.x.c))
                     if orient == "H" else (float(n.y.cx), float(n.y.cy), float(n.y.c)))
    x = min(xs, key=lambda v: (float(v.cx), float(v.cy), float(v.c)))
    y = min(ys, key=lambda v: (float(v.cx), float(v.cy), float(v.c)))
    w = max(rights, key=lambda v: (float(v.cx), float(v.cy), float(v.c))) - x
    h = max(bottoms, key=lambda v: (float(v.cx), float(v.cy), float(v.c))) - y
    return Node(f"{orient}Group", x, y, w, h, orient=orient, children=ordered)


def infer_tree(calls: list[Call], order: tuple[str, ...]) -> tuple[Node, int]:
    nodes = [make_node(c) for c in calls if c.ok]
    merges = 0
    while len(nodes) > 1:
        changed = False
        for orient in order:
            clusters = chain_clusters(nodes, orient)
            if not clusters:
                continue
            used = set()
            new_nodes = []
            for cluster in clusters:
                new_nodes.append(merge_group(cluster, orient))
                used.update(id(n) for n in cluster)
                merges += 1
            new_nodes.extend(n for n in nodes if id(n) not in used)
            nodes = new_nodes
            changed = True
        if not changed:
            break
    if len(nodes) == 1:
        return nodes[0], merges
    x = min((n.x for n in nodes), key=lambda v: float(v.c))
    y = min((n.y for n in nodes), key=lambda v: float(v.c))
    return Node("root", x, y, Lin(c=ONE), Lin(c=ONE), orient="?", children=nodes), merges


def shape(n: Node) -> str:
    if n.is_leaf():
        return "leaf"
    if n.orient in ("H", "V"):
        return f"{n.orient}{len(n.children)}"
    return "MIX"


def pattern_name(root: Node) -> str:
    s = shape(root)
    if s == "H3":
        return "H3 左中右 (固定-弹性-固定)"
    if s == "H2":
        child_shapes = [shape(c) for c in root.children]
        if "V3" in child_shapes:
            return "H_V 左 + 右(上中下)"
        if "V2" in child_shapes:
            return "H_V 左 + 右(上下)"
        return "H2 左右分布"
    if s == "V3":
        shapes = [shape(c) for c in root.children]
        if "H3" in shapes:
            return "V_H_V 上 / 左中右 / 下"
        return "V3 上中下"
    if s == "V2":
        shapes = [shape(c) for c in root.children]
        if shapes[0] == "H3":
            return "V_H 上(左中右) + 下"
        if shapes[-1] == "H3":
            return "V_H 上 + 下(左中右)"
        if "H2" in shapes:
            return "V_H 上(左右) + 下" if shapes[0] == "H2" else "V_H 上 + 下(左右)"
        return "V2 上下分布"
    if root.orient == "?" or s == "MIX":
        return "多区域嵌套（需人工确认）"
    return f"{s} 嵌套布局"


def dim_kind(expr: Lin, axis: str) -> str:
    coef = expr.cx if axis == "x" else expr.cy
    if abs(coef) <= TOL:
        return "fixed"
    if abs(coef - ONE) <= TOL:
        return "stretch(1)"
    return f"ratio({float(coef):g})"


def ascii_tree(n: Node, prefix: str = "", is_last: bool = True) -> list[str]:
    connector = "└─ " if is_last else "├─ "
    label = n.name if n.is_leaf() else f"{n.orient or 'ROOT'} [{pattern_dim(n)}]"
    line = prefix + connector + label
    if not n.is_leaf():
        line += f"  x={fmt(n.x)} y={fmt(n.y)} w={fmt(n.w)} h={fmt(n.h)}"
    out = [line]
    child_prefix = prefix + ("   " if is_last else "│  ")
    for i, c in enumerate(n.children):
        out.extend(ascii_tree(c, child_prefix, i == len(n.children) - 1))
    return out


def pattern_dim(n: Node) -> str:
    return f"{dim_kind(n.w, 'x')} / {dim_kind(n.h, 'y')}"


def safe_object_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "", name)
    s = re.sub(r"^(m_|IDC_)", "", s)
    if not s:
        s = "widget"
    if s[0].isdigit():
        s = "w" + s
    return s[0].lower() + s[1:]


def guess_widget(name: str, mapping: dict) -> str:
    key = re.sub(r"[^a-z0-9_]", "", re.sub(r"^idc_", "", name.lower()))
    if key in mapping:
        return mapping[key]
    low = name.lower()
    rules = (
        ("tree", "QTreeWidget"), ("table", "QTableView"), ("list", "QListWidget"),
        ("combo", "QComboBox"), ("edit", "QLineEdit"), ("btn", "QPushButton"),
        ("button", "QPushButton"), ("label", "QLabel"), ("static", "QLabel"),
        ("progress", "QProgressBar"), ("slider", "QSlider"), ("check", "QCheckBox"),
        ("radio", "QRadioButton"), ("tab", "QTabWidget"), ("status", "QLabel"),
        ("view", "QTableView"), ("chart", "QWidget"),
    )
    for token, widget in rules:
        if token in low:
            return widget
    return "QWidget"


def ui_xml(n: Node, mapping: dict, root: bool = False, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if n.is_leaf():
        cls = guess_widget(n.name, mapping)
        lines = [f'{pad}<widget class="{cls}" name="{safe_object_name(n.name)}">']
        if n.mfc_id:
            lines.append(f'{pad}  <property name="mfcId">')
            lines.append(f'{pad}   <string notr="true">{n.mfc_id}</string>')
            lines.append(f'{pad}  </property>')
        lines.append(f"{pad}  <!-- width: {dim_kind(n.w, 'x')}; height: {dim_kind(n.h, 'y')} -->")
        lines.append(f"{pad}</widget>")
        return lines
    cls = {"H": "QHBoxLayout", "V": "QVBoxLayout"}.get(n.orient, "QHBoxLayout")
    lines = [f'{pad}<layout class="{cls}" name="{safe_object_name(n.name)}Layout">']
    for child in n.children:
        lines.append(f"{pad}  <!-- stretch hint: {pattern_dim(child)} -->")
        lines.append(f"{pad}  <item>")
        lines.extend(ui_xml(child, mapping, False, indent + 2))
        lines.append(f"{pad}  </item>")
    lines.append(f"{pad}</layout>")
    return lines


def load_mapping(root: Path) -> dict:
    path = root / ".mfc-qt" / "config.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    result = {}
    for key, value in data.get("controlMap", {}).items():
        if isinstance(value, dict) and value.get("widget"):
            result[re.sub(r"[^a-z0-9_]", "", re.sub(r"^idc_", "", key.lower()))] = value["widget"]
        elif isinstance(value, str):
            result[re.sub(r"[^a-z0-9_]", "", re.sub(r"^idc_", "", key.lower()))] = value
    return result


def confidence(calls: list[Call], root: Node, merges: int) -> tuple[str, str]:
    total = len(calls)
    ok = sum(1 for c in calls if c.ok)
    if total == 0:
        return "无", "未找到可解析的几何调用"
    ratio = ok / total
    if root.orient == "?":
        return "低", f"仅 {ok}/{total} 个调用可解析，或控件之间存在无法合并的间隙"
    if ratio >= 0.9 and merges >= 1:
        return "高", f"{ok}/{total} 个调用可解析，形成 {merges} 个布局分组"
    if ratio >= 0.5:
        return "中", f"{ok}/{total} 个调用可解析，部分表达式需人工核对"
    return "低", f"仅 {ok}/{total} 个调用可解析"


def render_markdown(result: dict) -> str:
    lines = [f"# OnSize 布局推断：{result['file']}", ""]
    if not result["handlers"]:
        lines.append("未找到 OnSize/OnResize 函数体，也未找到包含多个几何调用的块。")
        return "\n".join(lines)
    for h in result["handlers"]:
        lines.append(f"## 函数体：{h['handler']}")
        lines.append("")
        lines.append("| 目标 | 调用 | x | y | w | h |")
        lines.append("|---|---|---|---|---|---|")
        for c in h["calls"]:
            lines.append("| `{target}` | {func} | {x} | {y} | {w} | {h} |".format(**c))
        lines.append("")
        if h["unknown"]:
            lines.append("未解析的几何调用：")
            for raw in h["unknown"]:
                lines.append(f"- `{raw}`")
            lines.append("")
        for idx, cand in enumerate(h["candidates"], 1):
            lines.append(f"### 候选 {idx}：{cand['pattern']}")
            lines.append("")
            lines.append(f"- 置信度：**{cand['confidence']}**（{cand['reason']}）")
            lines.append(f"- 合并策略：{cand['order']}")
            lines.append("")
            lines.append("```text")
            lines.extend(cand["tree"])
            lines.append("```")
            lines.append("")
            lines.append("`.ui` 布局骨架：")
            lines.append("")
            lines.append("```xml")
            lines.extend(cand["ui_xml"])
            lines.append("```")
            lines.append("")
        lines.append("下一步：确认控件语义后按 `../references/layout-patterns.md` 落地布局，删除 `ON_WM_SIZE` 与整个重排块。")
        lines.append("")
    return "\n".join(lines)


def analyze_file(path: Path, root: Path) -> dict:
    text = strip_comments(path.read_text(encoding="utf-8", errors="ignore"))
    mapping = load_mapping(root)
    handlers = []
    for name, body in find_bodies(text):
        symbols = local_symbols(body)
        calls = parse_calls(body, symbols)
        if not calls:
            continue
        candidates = []
        for order in (("V", "H"), ("H", "V")):
            tree, merges = infer_tree(calls, order)
            conf, reason = confidence(calls, tree, merges)
            candidates.append({
                "pattern": pattern_name(tree),
                "confidence": conf,
                "reason": reason,
                "order": "+".join(order),
                "merges": merges,
                "tree": ascii_tree(tree),
                "ui_xml": ui_xml(tree, mapping),
            })
        # deduplicate identical trees
        unique = []
        seen = set()
        for c in candidates:
            key = tuple(c["tree"])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        unique.sort(key=lambda c: (-c["merges"], 0 if c["confidence"] == "高" else 1))
        handlers.append({
            "handler": name,
            "calls": [
                {
                    "target": c.target,
                    "func": c.func,
                    "x": fmt(c.x), "y": fmt(c.y), "w": fmt(c.w), "h": fmt(c.h),
                    "parsed": c.ok,
                }
                for c in calls
            ],
            "unknown": [c.raw for c in calls if not c.ok],
            "candidates": unique,
        })
    return {"file": str(path), "handlers": handlers}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sources", nargs="+", type=Path, help="C++ source files")
    p.add_argument("--root", type=Path, default=Path.cwd(), help="project root holding .mfc-qt/config.json")
    p.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    p.add_argument("--ui-out", type=Path, help="write the best .ui XML fragment to this file")
    args = p.parse_args()

    results = [analyze_file(f, args.root) for f in args.sources]
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print(render_markdown(result))
            print()
    if args.ui_out:
        fragments = []
        for result in results:
            for h in result["handlers"]:
                if h["candidates"]:
                    fragments.extend(h["candidates"][0]["ui_xml"])
        if fragments:
            args.ui_out.parent.mkdir(parents=True, exist_ok=True)
            args.ui_out.write_text("\n".join(fragments) + "\n", encoding="utf-8")
            print(f"wrote {args.ui_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
