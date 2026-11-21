---
name: mfc-layout-onsize
description: This skill should be used when converting MFC OnSize/WM_SIZE handlers that manually reposition or resize child controls into Qt Widgets .ui layout structures using QBoxLayout, QGridLayout, QFormLayout, size policies, stretch factors and QSplitter. Triggers include OnSize, WM_SIZE, 手动调整布局, 控件随窗口缩放.
agent_created: true
---

# MFC OnSize → Qt 布局

## Overview

把 MFC 在 `OnSize()` / `WM_SIZE` 中手工计算并 `MoveWindow` 子控件位置的代码，改为 `.ui` 中的 QLayout 结构。**目标：删除手工重排代码，让布局管理器自动响应尺寸变化。**

## Guardrails

- 子控件几何一律由 QLayout 管理；删除 `OnSize` 中的 `MoveWindow`/`SetWindowPos` 调用。
- 不在 `resizeEvent()` 中调用 `setGeometry()` 重排由布局管理的子控件；布局会覆盖这些设置。
- `.ui` 中用嵌套布局 + stretch + sizePolicy 表达 MFC 代码里的比例关系（如"左栏固定 200px，右栏占满"）。
- `resizeEvent()` 仅在确有自定义绘制缓存、滚动条范围等派生计算时覆写，且必须调用基类实现。
- 结果必须支持最小/最大窗口、高 DPI，以及 Qt Designer 中再编辑。

## Workflow

1. **自动推断布局意图**：对含 `OnSize` / `OnResize` 的 `.cpp` 运行脚本，它把 `MoveWindow` / `SetWindowPos` 的坐标解析为 `a*cx + b*cy + c`，再合并相邻控件得到布局树、模式名、置信度和 `.ui` 骨架：

   ```bash
   python scripts/onsize_layout_infer.py MyDlg.cpp --root <项目根>
   python scripts/onsize_layout_infer.py MyDlg.cpp --root <项目根> --ui-out layout.xml
   python scripts/onsize_layout_infer.py MyDlg.cpp --root <项目根> --json
   ```

   脚本会读取 `.mfc-qt/config.json` 的 `controlMap`，用用户自定义映射决定骨架中的 widget class。推断规则见 `references/intent-inference.md`，模式库见 `references/layout-patterns.md`。

2. **读懂并确认意图**：脚本输出只是建议，必须结合控件语义复核：
   - 按比例分配 → stretch factor。
   - 固定尺寸 + 剩余占满 → `setFixedSize` / `sizePolicy` + stretch。
   - 用户可拖拽分隔 → `QSplitter`。
   - 分组框内重排 → `QGroupBox` + 内部布局。
   - 多页切换 → `QStackedWidget`。
   - 置信度为"低"或出现多个候选时，以人工设计为准。

3. **设计布局树**：自顶向下画出 `QWidget → QVBoxLayout → (QHBoxLayout, QHBoxLayout, ...)`。脚本给出的模式名对应：左中右 `H3`、上下 `V2`、上+左中右 `V_H`、左+上中下 `H_V`、上/左中右/下 `V_H_V`、网格 `G`。结合 `references/onsize-patterns.md` 与 `references/layout-patterns.md` 确定最终树。

4. **在 `.ui` 中落地**：把脚本的 XML 骨架嵌入 `<widget>` 的 `<layout>` 节点；用嵌套布局替代坐标；为每个容器设置合理 margin/spacing；按骨架注释设置 stretch 与 sizePolicy，并补 minimumSize/maximumSize。
5. **删除旧代码**：移除 `ON_WM_SIZE` 映射和 `OnSize()` 中的重排逻辑；如保留 `resizeEvent()`，只做派生的绘制/计算。
6. **验证**：拖动窗口从最小到最大、最大化/还原、切换 DPI 缩放，确认无重叠、截断或空白异常。

## Pattern Quick Reference

| MFC OnSize 行为 | Qt 布局 |
|---|---|
| 控件宽度 = `cx/2` | `QHBoxLayout` + 两个 stretch=1 的子布局 |
| 工具栏固定高、客户区占满 | 根 `QVBoxLayout`：工具栏 sizePolicy=Fixed，客户区 Expanding |
| 按钮始终靠右下 | 布局末尾 `QSpacerItem` 水平+垂直 Expanding |
| 左树固定宽、右表占满 | `QHBoxLayout`：左 `setFixedWidth`，右 stretch=1；或 `QSplitter` |
| 表格随窗口铺满 | 把 `QTableView` 直接放进 stretch=1 的布局 |
| 保持宽高比 | 自定义 widget 覆写 `heightForWidth()`，或外层布局配 `QSizePolicy` |
| `GetClientRect` 后按比例缩放 | 通常整段删除，交给布局 |

## Example

```cpp
// MFC：手动把编辑框和列表框按窗口宽度对半分
void CMyDlg::OnSize(UINT nType, int cx, int cy) {
    CDialogEx::OnSize(nType, cx, cy);
    if (m_edit.GetSafeHwnd() && m_list.GetSafeHwnd()) {
        m_edit.MoveWindow(10, 10, cx/2 - 15, cy - 20);
        m_list.MoveWindow(cx/2 + 5, 10, cx/2 - 15, cy - 20);
    }
}

// Qt：.ui 中 QHBoxLayout 两个 stretch=1 的子布局，C++ 无重排代码
// 根 layout = QHBoxLayout
//   ├─ QVBoxLayout (stretch 1) → edit
//   └─ QVBoxLayout (stretch 1) → list
// OnSize / resizeEvent 全部删除
```

若确实需要在尺寸变化时更新派生数据（例如重算图表刻度）：

```cpp
void MyWidget::resizeEvent(QResizeEvent *event) {
    QWidget::resizeEvent(event);            // 必须调用基类
    recomputeScale(event->size());          // 只做派生计算，不 setGeometry 子控件
}
```

## Common Mistakes

- 迁移后仍保留 `OnSize` 空函数与 `ON_WM_SIZE` 映射，混淆维护者。
- 用 `setFixedSize()` 固定了本应自适应控件，窗口放大后留大片空白。
- 嵌套布局缺少 stretch，导致所有控件等分而不符合原比例。
- 在 `resizeEvent()` 里反复 `setGeometry()` 与布局打架，出现抖动。
- 忽略 `minimumSizeHint()`，窗口缩到很小时控件重叠。

## Bundled References

- `references/onsize-patterns.md`：常见 OnSize 算式 → 布局结构对照。
- `references/layout-patterns.md`：布局模式库（H2/H3/V2/V_H/H_V/V_H_V/G/FORM 等）。
- `references/intent-inference.md`：几何表达式线性化、分组判据、固定/拉伸判定与置信度。
- `references/layout-api-notes.md`：sizePolicy、stretch、QSplitter、QStackedWidget 使用要点。
- `scripts/onsize_layout_infer.py`：从 C++ 自动推断布局树并输出 `.ui` 骨架。

## Output Shape

1. 原 OnSize 逻辑意图分析（几何表 + 推断出的模式名 + 置信度）
2. 布局树设计（层级 + stretch + sizePolicy，含 `.ui` XML 骨架）
3. `.ui` 改动说明与控件位置表达
4. 删除的旧代码清单
5. 保留 `resizeEvent()` 的理由与内容（如有）
6. 多尺寸/多 DPI 验证结果

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。QLayout / QSizePolicy / QSplitter 在 Qt 5 与 Qt 6 间基本一致。
- 间距一律用 `layout->setContentsMargins(...)`，不用 Qt 6 已移除的 `setMargin()`。
- 生成 `.ui` 时不要写版本专属属性；差异总表见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
