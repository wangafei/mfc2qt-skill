# SendMessage / PostMessage 替换表

## 基本映射

| MFC 调用 | 语义 | Qt 替换 |
|---|---|---|
| `pWnd->SendMessage(WM_X, wp, lp)` 同线程 | 同步调用并处理返回 | 直接调用槽函数或 `emit` 信号（直接连接） |
| `pObj->SendMessage(...)` 跨线程 | 同步等待 GUI 处理 | `QMetaObject::invokeMethod(obj, slot, Qt::BlockingQueuedConnection, ...)` + `Q_RETURN_ARG` |
| `pWnd->PostMessage(WM_X, wp, lp)` | 异步投递 | `QMetaObject::invokeMethod(obj, slot, Qt::QueuedConnection, ...)` 或 `postEvent` |
| `::SendMessage(HWND_BROADCAST, ...)` | 广播 | 应用级信号 / IPC（见 message-conversion） |
| `SendNotifyMessage` | 同线程同步、跨线程异步 | 按当前线程判断，用上述对应方式 |
| `SendMessageTimeout` | 带超时的同步 | 避免阻塞 GUI；用 queued + 回执信号实现超时逻辑 |
| `GetMessage`/`PeekMessage`/`DispatchMessage` | 消息泵 | Qt 事件循环（`QCoreApplication::exec()`），不手工处理 |

## 连接类型速查

| Qt::ConnectionType | 行为 | 对应 |
|---|---|---|
| `AutoConnection`（默认） | 同线程直接，跨线程排队 | 大多数情况 |
| `DirectConnection` | 总是在发送者线程立即执行 | 同线程 `SendMessage` |
| `QueuedConnection` | 总在接收者线程事件循环执行 | `PostMessage` |
| `BlockingQueuedConnection` | 排队并阻塞等待返回 | 跨线程 `SendMessage`，注意死锁 |
| `UniqueConnection` | 与其他类型按位或，避免重复连接 | 防重复订阅 |

## 跨线程同步调用示例

```cpp
// worker 线程中同步请求 GUI 线程计算并取回结果
int result = 0;
QMetaObject::invokeMethod(pMainWnd, "computeValue",
                          Qt::BlockingQueuedConnection,
                          Q_RETURN_ARG(int, result),
                          Q_ARG(int, input));

// GUI 对象需声明为 slot 或 Q_INVOKABLE
public slots:
    int computeValue(int input);
```

**死锁警告**：不要在 GUI 线程对 GUI 对象使用 `BlockingQueuedConnection`；接收者所在线程正被自己阻塞。跨线程同步调用只适用于 worker → GUI 方向，且 GUI 处理不能反过来等待 worker。

## 异步投递示例

```cpp
// 方式一：invokeMethod 带参数（槽或 Q_INVOKABLE）
QMetaObject::invokeMethod(pMainWnd, "appendLog",
                          Qt::QueuedConnection,
                          Q_ARG(QString, message));

// 方式二：lambda（Qt 5.10+/6）
QMetaObject::invokeMethod(pMainWnd, [pMainWnd, message]() {
    pMainWnd->appendLog(message);
}, Qt::QueuedConnection);

// 方式三：信号 + queued 连接（在连接时指定）
connect(worker, &Worker::logReady, pMainWnd, &MainWnd::appendLog,
        Qt::QueuedConnection);
```

## 返回值处理

原 `SendMessage` 依赖 `LRESULT` 返回值时：

1. 最简：把状态写入共享的结果对象/结构体，或用同步 `invokeMethod` 的 `Q_RETURN_ARG`。
2. 异步场景：定义"请求 ID + 结果信号"，发送方连接结果信号，通过 ID 匹配异步回执。
3. 避免用全局变量传返回值。

## 检查项

- [ ] 所有 SendMessage/PostMessage 调用点已替换，无 Win32 消息 API 残留。
- [ ] 跨线程投递使用 queued 方式，GUI 对象不被直接跨线程访问。
- [ ] 无 GUI 线程上的 BlockingQueuedConnection。
- [ ] 同步语义场景确认返回值/状态时序一致。
- [ ] 载荷数据用值类型或智能指针，无悬空指针。
