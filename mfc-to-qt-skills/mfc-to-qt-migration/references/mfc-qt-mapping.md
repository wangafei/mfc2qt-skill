# MFC → Qt 对照总表

先查此表定位改造方向，再到专项技能看细节。Qt 侧`控件`均指 `.ui` 中的 QWidget 子类，`name` 为建议 objectName。

## 类与窗口

| MFC | Qt Widgets | 备注 |
|---|---|---|
| `CWnd` | `QWidget` | 所有窗口基类 |
| `CFrameWnd` / `CMDIFrameWnd` | `QMainWindow` | 主窗口、菜单、工具栏、状态栏 |
| `CMDIChildWnd` | `QMdiSubWindow` + `QMdiArea` | 替代 MDI |
| `CDialog` / `CDialogEx` | `QDialog` + `.ui` | 见 `mfc-dialog-lifecycle` |
| `CPropertySheet` | `QDialog` + `QTabWidget`，或 `QWizard` | 属性页 |
| `CScrollView` | `QAbstractScrollArea` 子类 | 滚动视图 |
| `CView` / `CFormView` | `QWidget` + `.ui` | 文档视图结构需自行拆分 |
| `CControlBar` / `CToolBar` | `QToolBar` | |
| `CStatusBar` | `QStatusBar` | |
| `CListCtrl` | `QTreeWidget` / `QTableView` + model | 大量数据用 model/view |
| `CTreeCtrl` | `QTreeWidget` / `QTreeView` + model | |
| `CListBox` | `QListWidget` / `QListView` | |
| `CComboBox` | `QComboBox` | |
| `CEdit` | `QLineEdit` / `QTextEdit` | 单行/多行 |
| `CButton` | `QPushButton` / `QCheckBox` / `QRadioButton` | 按 BS_* 样式区分 |
| `CStatic` | `QLabel` | |
| `CProgressCtrl` | `QProgressBar` | |
| `CSliderCtrl` | `QSlider` | |
| `CSpinButtonCtrl` | `QSpinBox` / `QDoubleSpinBox` | |
| `CTabCtrl` | `QTabWidget` | |
| `CDateTimeCtrl` | `QDateEdit` / `QTimeEdit` / `QDateTimeEdit` | |
| `CString` | `QString` | |
| `CRect` | `QRect` | |
| `CPoint` / `CSize` | `QPoint` / `QSize` | |
| `CDC` / `CPaintDC` | `QPainter` | 在 `paintEvent()` 中使用 |
| `CFont` | `QFont` | |
| `CBitmap` / `CImage` | `QPixmap` / `QImage` | |
| `CBrush` / `CPen` | `QBrush` / `QPen` | |

## 消息映射宏 → 信号槽 / 事件

| MFC 宏 | Qt 做法 |
|---|---|
| `ON_BN_CLICKED(id, fn)` | `connect(ui->btn, &QPushButton::clicked, this, &Class::fn)` |
| `ON_COMMAND(id, fn)` | `connect(action, &QAction::triggered, ...)` |
| `ON_COMMAND_RANGE` | 遍历 QAction/QButtonGroup，或用 `QSignalMapper`/lambda 捕获 id |
| `ON_UPDATE_COMMAND_UI` | 状态变化时 `setEnabled()` / `setChecked()`；或 `QAction::changed` |
| `ON_NOTIFY(code, id, fn)` | 控件专属信号，如 `itemClicked`、`valueChanged` |
| `ON_CBN_SELCHANGE` | `QComboBox::currentIndexChanged` |
| `ON_EN_CHANGE` | `QLineEdit::textChanged` / `QTextEdit::textChanged` |
| `ON_LBN_SELCHANGE` | `QListWidget::currentRowChanged` |
| `ON_WM_SIZE` | `resizeEvent()` 或优先用 QLayout |
| `ON_WM_PAINT` | `paintEvent()` |
| `ON_WM_CLOSE` | `closeEvent()` / `rejected` 信号 |
| `ON_WM_TIMER` | `QTimer::timeout` |
| `ON_MESSAGE(WM_USER+n)` | 自定义信号 / `QEvent::registerEventType()` |
| `ON_REGISTERED_MESSAGE` | `QEvent::registerEventType()` + 自定义 QEvent |
| `ON_WM_KEYDOWN` / `ON_WM_CHAR` | `keyPressEvent()` |
| `ON_WM_LBUTTONDOWN` 等 | `mousePressEvent()` / `eventFilter()` |
| `PreTranslateMessage` | `eventFilter()` 或 `QShortcut` |

## 数据绑定

| MFC | Qt |
|---|---|
| `DDX_Text(pDX, IDC_EDIT, m_str)` | `ui->edit->text()` 或 `QString` 成员 + `textChanged` 信号 |
| `DDX_Check` | `ui->check->isChecked()` / `checkState()` |
| `DDX_Radio` | `QButtonGroup::checkedId()` |
| `DDX_CBIndex` | `QComboBox::currentIndex()` |
| `DDX_LBString` | `QListWidget::currentItem()->text()` |
| `DDV_MaxChars` | `QLineEdit::setMaxLength()` / `QValidator` |
| `DDV_MinMaxInt` | `QSpinBox::setRange()` / `QIntValidator` |
| `UpdateData(TRUE)` | 从 `ui->` 控件读取到数据对象 |
| `UpdateData(FALSE)` | 从数据对象写入 `ui->` 控件 |
| `DoDataExchange()` | 删除；改为显式 `readFromUi()` / `writeToUi()` |

## 几何与布局

| MFC | Qt |
|---|---|
| `MoveWindow(hwnd, x, y, w, h, TRUE)` | 子控件删除，交给 QLayout；仅顶层 `setGeometry()` |
| `GetWindowRect()` | `frameGeometry()`（含标题栏）/ 顶层用 `geometry()` |
| `GetClientRect()` | `rect()` / `contentsRect()` |
| `SetWindowPos(..., HWND_TOPMOST)` | `setWindowFlags(Qt::WindowStaysOnTopHint)` + `show()` |
| `ScreenToClient(pt)` | `mapFromGlobal(pt)` |
| `ClientToScreen(pt)` | `mapToGlobal(pt)` |
| `CenterWindow()` | 屏幕可用区中心 + `move()` |
| `OnSize()` + 手算子控件位置 | QBoxLayout / QGridLayout + stretch + sizePolicy |
| `GetSystemMetrics(SM_CXSCREEN)` | `QGuiApplication::primaryScreen()->availableGeometry()` |

## 生命周期

| MFC | Qt |
|---|---|
| `dlg.DoModal()` | `QDialog dlg(this); dlg.exec();` 或成员 `QDialog*` |
| `dlg.Create(IDD, parent); dlg.ShowWindow(...)` | `new QDialog(parent); setAttribute(Qt::WA_DeleteOnClose); show();` |
| `EndDialog(IDOK)` | `accept()` / `done(QDialog::Accepted)` |
| `EndDialog(IDCANCEL)` | `reject()` / `done(QDialog::Rejected)` |
| `DestroyWindow()` | `deleteLater()` / 关闭时自动销毁 |
| `OnInitDialog()` | 构造函数中 `setupUi()` 之后，或 `showEvent()` 一次性逻辑 |
| `PostNcDestroy` 中 `delete this` | `WA_DeleteOnClose` 或父对象所有权 |
| `AfxMessageBox()` | `QMessageBox::information/warning/critical` |
| `CFileDialog` | `QFileDialog::getOpenFileName()` 等 |
