---
name: mfc-message-to-slot
description: This skill should be used when converting MFC ON_MESSAGE handlers, custom WM_USER/WM_APP messages, registered messages, SendMessage and PostMessage calls to Qt signals and slots, QEvent, QMetaObject::invokeMethod and QCoreApplication::postEvent. Triggers include ON_MESSAGE, WM_USER, SendMessage, PostMessage, 自定义消息, RegisterWindowMessage.
agent_created: true
---

# MFC 自定义消息 → Qt 信号槽

## Overview

把 MFC 中通过 `ON_MESSAGE` / `ON_REGISTERED_MESSAGE` 处理的自定义消息，以及 `SendMessage` / `PostMessage` 调用，改为 Qt 的信号槽、自定义 QEvent 和 `QMetaObject::invokeMethod`。范围限定为**窗口消息机制**；控件通知宏见 `mfc-macro-to-slot`，键鼠消息见 `mfc-input-events`。

## Guardrails

- 删除 `ON_MESSAGE` / `ON_REGISTERED_MESSAGE` 宏与 `LRESULT OnXxx(WPARAM, LPARAM)` 处理器签名。
- 优先用**信号**表达"发生了什么"；只有当需要拦截 Qt 已定义的事件流时才用 `event()` / `eventFilter()` + 自定义 QEvent。
- 同步语义（原 `SendMessage`）用直接信号/槽调用或 `QMetaObject::invokeMethod(..., Qt::BlockingQueuedConnection)`（仅跨线程且确认无死锁风险）。
- 异步语义（原 `PostMessage`）用 `Qt::QueuedConnection` 或 `QCoreApplication::postEvent()`。
- 严禁在非 GUI 线程直接调用 QWidget 方法；跨线程投递到 GUI 对象。
- `WPARAM`/`LPARAM` 中打包的数据必须转为有类型的参数或自定义 QEvent 字段，不再用 `reinterpret_cast` 传指针穿过消息链。

## Decision Guide

| 原消息特征 | Qt 方案 |
|---|---|
| 窗口间通知、无返回数据 | 自定义信号 + `connect` |
| 需要跨线程投递到 GUI | `QMetaObject::invokeMethod(receiver, ..., Qt::QueuedConnection)` |
| 需要同步返回值且跨线程 | `invokeMethod(..., Qt::BlockingQueuedConnection)` + `Q_RETURN_ARG`（谨慎） |
| 需要携带复杂载荷 | 自定义 QEvent 子类，字段类型安全 |
| 全局/应用级广播 | 应用级信号（如主窗口单例的信号） |
| 模拟 `WM_COPYDATA` 传字符串/字节 | 信号携带 `QString`/`QByteArray` |
| 定时触发消息 | `QTimer::timeout` |
| 消息编号注册（`RegisterWindowMessage`） | `QEvent::registerEventType()` |

## Workflow

1. 列出所有 `ON_MESSAGE(id, handler)` / `ON_REGISTERED_MESSAGE`，查 `references/message-conversion.md` 决定信号还是 QEvent。
2. 为每个消息定义语义清晰的Qt信号（如 `void dataArrived(const QByteArray &payload);`），在发送方声明、源码中 `emit`。
3. 把原 handler 逻辑改为槽函数，去掉 `WPARAM`/`LPARAM`，改用类型化参数。
4. 替换所有 `SendMessage` / `PostMessage` 调用点；查 `references/send-post-mapping.md`。
5. 对跨线程场景，确认接收者线程亲和：GUI 对象只能在 GUI 线程被直接访问；用 queued 连接投递。
6. 验证消息顺序、同步/异步语义与返回值行为是否保持一致。

## Example

```cpp
// ---- MFC ----
#define WM_DATA_READY (WM_USER + 100)
BEGIN_MESSAGE_MAP(CMainDlg, CDialogEx)
    ON_MESSAGE(WM_DATA_READY, &CMainDlg::OnDataReady)
END_MESSAGE_MAP()

LRESULT CMainDlg::OnDataReady(WPARAM wp, LPARAM lp) {
    auto *data = reinterpret_cast<MyData*>(lp);
    Refresh(data);
    return 0;
}
// 发送
pDlg->SendMessage(WM_DATA_READY, 0, reinterpret_cast<LPARAM>(newData));

// ---- Qt ----
// 声明
signals:
    void dataReady(const MyData &data);
private slots:
    void onDataReady(const MyData &data);

// 连接（构造函数）
connect(this, &MainDialog::dataReady, this, &MainDialog::onDataReady);

// 发送（同线程，直接发出）
emit dataReady(myData);

// 跨线程（从 worker 线程投递到 GUI 线程的对象）
QMetaObject::invokeMethod(pDlg, [pDlg, data]() { emit pDlg->dataReady(data); },
                          Qt::QueuedConnection);
```

注意：跨线程时不要在 worker 线程直接 `emit pDlg->dataReady(...)` 并期望立即执行；`connect` 的 connection type 或 `invokeMethod` 的方式决定实际执行线程。对 GUI 接收者使用 queued 连接。

## Common Mistakes

- 用 `QEvent::Type` 强转整数消息 ID 与 Qt 内建事件冲突；应使用 `QEvent::registerEventType()` 注册。
- `SendMessage` 直接改成 `emit` 却依赖同步返回值，导致后续代码读到旧状态。
- `BlockingQueuedConnection` 在 GUI 线程调用并等待 GUI 线程处理，造成死锁。
- 通过 `LPARAM` 传递裸指针，对象生命周期不清晰导致悬空。
- 忘记在类声明加 `Q_OBJECT`，信号无法 `emit`/`connect`。
- 在 worker 线程直接调用 `ui->` 更新界面。

## Bundled References

- `references/message-conversion.md`：消息类型 → 信号/QEvent 决策与自定义 QEvent 模板。
- `references/send-post-mapping.md`：SendMessage/PostMessage 替换表与线程语义。

## Output Shape

1. 消息清单（ID、来源、载荷、同步性、线程）
2. 每个消息的信号/QEvent 设计
3. 处理器改造与连接代码
4. 所有调用点替换说明（含线程投递方式）
5. 行为等价性验证（顺序、返回值、生命周期）

## Qt 版本适配

- 先读 `<项目根>/.mfc-qt/config.json` 的 `qt.resolvedMajor`。
- `QMetaObject::invokeMethod` 的函数指针重载在 Qt 5.10+ 与 Qt 6 都可用；字符串式调用只在必要时使用且要注意参数类型名。
- `nativeEvent()` 的结果参数在 Qt 5 是 `long *result`、Qt 6 是 `qintptr *result`；用 `QT_VERSION_CHECK(6, 0, 0)` 条件编译隔离在平台层。
- 其他差异见 `../mfc-to-qt-migration/references/qt-version-compat.md`。

Prefer Chinese explanations when the user writes in Chinese.
