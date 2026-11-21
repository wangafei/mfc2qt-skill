# 消息 → 信号 / QEvent 转换

## 决策树

1. 消息只是"通知某事发生"，接收方处理后无返回值 → **信号 + 槽**。
2. 需要携带结构化数据 → 信号参数用值类型/`QSharedPointer`；或自定义 QEvent 携带字段。
3. 需要拦截 Qt 内建事件（如 focus、show、close）→ 覆写对应事件处理器，自定义消息另用 `event()`。
4. 消息来自 worker 线程 → 信号 + queued 连接，或 `QMetaObject::invokeMethod`。
5. 全局唯一消息、多个监听者 → 应用级单例信号，或 `QEventBus` 模式（项目自建）。

## 自定义 QEvent 模板

```cpp
// 注册唯一事件类型（头文件声明 extern 或在 cpp 静态保存）
static int dataReadyEventType = QEvent::registerEventType();

class DataReadyEvent : public QEvent {
public:
    explicit DataReadyEvent(QByteArray payload)
        : QEvent(QEvent::Type(dataReadyEventType)), m_payload(std::move(payload)) {}

    const QByteArray &payload() const { return m_payload; }
    static QEvent::Type type() { return QEvent::Type(dataReadyEventType); }

private:
    QByteArray m_payload;
};

// 接收方覆写 event()
bool MainDialog::event(QEvent *e) {
    if (e->type() == DataReadyEvent::type()) {
        auto *de = static_cast<DataReadyEvent *>(e);
        onDataReady(de->payload());
        return true;
    }
    return QDialog::event(e);
}

// 投递（异步，类似 PostMessage）
QCoreApplication::postEvent(receiver, new DataReadyEvent(bytes));
```

事件对象由 Qt 接管所有权（投递后不要手动 delete）；同步派发用 `QCoreApplication::sendEvent(receiver, &event)`（栈对象即可，类似 SendMessage 但不跨线程）。

## WM_USER / WM_APP / 注册消息

| MFC | Qt |
|---|---|
| `#define WM_XXX (WM_USER+n)` | 直接定义信号；若用 QEvent 则 `QEvent::registerEventType()` |
| `RegisterWindowMessage("...")` | 无需注册表级 ID；用信号名或已注册的 QEvent 类型 |
| 消息 ID 跨进程 | Qt 无等价内建机制；用 `QLocalSocket` / IPC 明确传消息 |
| `WM_COPYDATA` | 信号携带 `QString`/`QByteArray`；跨进程用 `QLocalSocket`/共享内存 |

不要复用 Qt 保留的事件类型区间（0–`QEvent::User`）；自定义类型从 `QEvent::registerEventType()` 获取。

## 定时器消息

| MFC | Qt |
|---|---|
| `SetTimer` + `ON_WM_TIMER` | `QTimer *t = new QTimer(this); connect(t, &QTimer::timeout, ...); t->start(ms);` |
| `KillTimer` | `t->stop()` |
| 一次性定时 | `QTimer::singleShot(ms, this, slot)` |
| 定时器 ID 区分 | 多个 QTimer 对象，或用 `sender()` 区分 |

## 广播与全局通知

MFC 中 `SendMessage(HWND_BROADCAST, ...)` 或 `::PostMessage(NULL, ...)`：Qt 中没有直接等价的窗口广播。可选方案：

- 进程内：主窗口/控制器对象发出信号，所有关注方连接。
- 跨进程：`QLocalServer`/`QLocalSocket` 或 `QSharedMemory` + 明确的协议。
- 系统级事件（如设备插入）：用平台 API 后统一转成 Qt 信号，隔离在平台层。

## 数据生命周期

- 信号参数用值语义（`QString`、`QByteArray`、结构体）避免悬空指针。
- 必须用指针时，用 `QSharedPointer<T>` 或 `QObject` 父子所有权，明确释放时机。
- 原 `SendMessage` 中 `new` 出来、`PostMessage` 后接收方 `delete` 的模式，改为值传递或智能指针。
