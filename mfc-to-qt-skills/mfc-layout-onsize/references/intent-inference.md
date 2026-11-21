# OnSize 代码意图推断规则

`../scripts/onsize_layout_infer.py` 用以下规则把 C++ 几何算式转成布局树。了解规则有助于判断输出是否可信。

## 1. 支持的调用形式

```cpp
m_edit.MoveWindow(10, 20, cx/2 - 15, cy - 40);
pList->MoveWindow(0, 0, cx, cy, TRUE);
::MoveWindow(hwnd, 0, cy-40, cx, 40, TRUE);
pWnd->SetWindowPos(nullptr, nullptr, 200, 0, cx-200, cy, SWP_NOZORDER);
m_split.SetWindowPos(NULL, x, y, w, h, SWP_NOACTIVATE | SWP_NOZORDER);
```

只分析 `OnSize` / `OnResize` / `OnSizeChanged` 等函数体，以及包含 2 个以上几何调用的其它函数体。`ShowWindow(SW_HIDE)`、`Invalidate()` 等不参与几何推断，但会作为"多页/可见性"线索输出。

## 2. 表达式表示

每个坐标被解析为关于 `cx`、`cy` 的**线性式**：

```text
expr = a*cx + b*cy + c      (a,b,c 为有理数)
```

- `cx/2 - 15` → `(1/2)*cx + 0*cy - 15`
- `cy - 40` → `0*cx + 1*cy - 40`
- `rect.Width()` → `cx`；`rc.right` → `cx`；`rc.left`/`rc.top` → `0`
- 局部变量 `int w = cx - 200;` 会先被代入后续调用
- 无法解析的表达式（函数调用、三元表达式、`max()` 等）记为 unknown，相关控件置信度降低

## 3. 分组判据

两个控件/子布局能合成一个水平组，当且仅当：

1. 两者的 `y` 线性式相等，`h` 线性式相等（允许纯常量间距差）；
2. 前者 `x + w` 与后者 `x` 的差是**纯常量**（>= 0，作为 spacing）；
3. 合并后的包围盒 = 左控件 x 到右控件右边界，y/h 不变。

垂直组同理：相等的 x/w，y 方向相邻，差为纯常量。

先分别尝试"纵向优先"和"横向优先"两种合并顺序，得到两个候选树，取合并数更多、覆盖率更高的候选；若两者接近则都输出让用户选择。

## 4. 固定 / 拉伸判定

对节点宽度表达式 `w = a*cx + b*cy + c`：

| 系数 | 含义 | Qt 表达 |
|---|---|---|
| `a = 0, b = 0` | 固定尺寸 | `setFixedWidth(c)` 或 `sizePolicy=Fixed` + `maximumWidth` |
| `a = 1` | 占满父宽度 | stretch=1（若同层有多个 stretch，按系数比例分配） |
| `a = 1/2`、`1/3` | 比例 | stretch 按比例整数化，如 1/2 : 1/2 → 1:1；1/3 : 2/3 → 1:2 |
| `a` 为其它 | 复杂比例 | 人工确认；可能需要自定义 layout |

高度同理看 `b`。常量 `c` 只作 margin/spacing 参考，不生成 sizePolicy。

## 5. 模式命名

脚本按根节点的形状与系数给模式名（详见 `layout-patterns.md`）：

- `H2` / `V2`：左右 / 上下
- `H3`：左中右（fixed-stretch-fixed）
- `V_H` / `H_V`：上+左中右 / 左+上中下
- `V_H_V`：上 / 左中右 / 下
- `G`：多行多列且对齐
- `FILL` / `CORNER` / `FORM` / `SPLITTER` / `STACK` / `SCROLL`

名字只是提示，**必须结合控件语义确认**。例如 `H3` 的中间控件若是属性页而非主视图，可能实际应为 `QStackedWidget`。

## 6. 置信度

- 高：所有几何调用可解析，分组无歧义，覆盖 >= 80% 控件。
- 中：存在少量 unknown 或间距含变量，但主体结构清晰。
- 低：大量 unknown、控件重叠或分组互相矛盾；此时脚本只输出原始几何表，应人工设计布局。

## 7. 输出到 .ui 的映射

- `H` → `<layout class="QHBoxLayout" name="...">`
- `V` → `<layout class="QVBoxLayout" name="...">`
- 叶子 → `<widget class="..." name="..."/>`
- 每个叶子保留 `mfcId` 动态属性（若原 ID 已知）
- stretch 与 sizePolicy 以 XML 注释形式写在对应 item 内，由人在 Qt Designer 中设置或以 C++ `layout->setStretch()` 补充
- 生成的片段不是完整 `.ui` 文件；要嵌入 `<widget class="QDialog">` 的 `<layout>` 节点中

## 8. 人工复核清单

- [ ] 模式名与界面语义一致（树/表/属性/状态栏）。
- [ ] 固定宽度确实不该随窗口变化（高 DPI 下常量像素可能不合适）。
- [ ] 中间弹性区域设置了合理 `minimumSize`，窗口缩小时不塌陷。
- [ ] 有分隔条拖动逻辑的改为 `QSplitter`。
- [ ] 删除了 `ON_WM_SIZE` 映射与整个 `OnSize` 重排块，或仅保留派生计算用的 `resizeEvent()`。
