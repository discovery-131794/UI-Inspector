from __future__ import annotations
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt
from uiautomation import Control, Rect
import uiautomation as auto
from win32api import GetSystemMetrics
from win32con import *
from uiinspector.core.pyjab import JDriver, JABException, JElement
from uiinspector.core.tree.jabtree import JABSelectorHelper, JABTreeItem
from uiinspector.core.tree.uiatree import UIASelectorHelper, UIATreeItem
from uiinspector.win32.functions import *
from uiinspector.win32.structures import *
from uiinspector.core.base import UITreeItem
import sys
import mouse, keyboard
import win32gui, win32api
import comtypes
import uiinspector.icons
from uiinspector import *
from typing import Tuple, cast

def to_tuple(rect: Rect|None) -> Tuple[int, int, int, int]:
    if isinstance(rect, Rect):
        return rect.left, rect.top, rect.right, rect.bottom
    return 0, 0, 0, 0
    

class ScreenManager:
    def __init__(self, window: MainWindow):
        self.window = window
        self.enabled = False
        self.hwnd = None
        self.monitor = (0, 0, GetSystemMetrics(0), GetSystemMetrics(1))
        self.last_rect = None

        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.draw_rect)

        self.countdown_timer = QtCore.QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.show_countdown)

        self.hinst = win32gui.GetModuleHandle(None)
        self.highlight_widget = None # highlight rect

    def start(self):
        mouse.hook(self.on_mouse_click)
        keyboard.hook(self.on_key_down)
        self.enabled = True
        self.timer.start()
        if self.hwnd:
            self.block_input()
        else:
            self.create_window()

    def close(self):
        # self.window.enable_windows()
        mouse.unhook(self.on_mouse_click)
        keyboard.unhook(self.on_key_down)
        self.enabled = False

    def on_mouse_click(self, event):
        if isinstance(event, mouse.ButtonEvent):
            self.show_selector()

    def on_key_down(self, event: keyboard.KeyboardEvent):
        if event.name == 'f2':
            self.delay()
        elif event.name == 'esc':
            self.quit()
        elif event.name == 'enter':
            self.show_selector()

    def show_selector(self):
        if self.enabled:
            self.close()
            self.window.show_selector_signal.emit()

    def delay(self):
        """
        delay 5 seconds, then continue control indication
        """
        self.window.delay_signal.emit()

    def quit(self):
        """
        quit control indication process
        """
        self.window.quit_signal.emit()

    def draw_rect(self):
        control = auto.ControlFromCursor()
        if control is None:
            return

        rect = control.BoundingRectangle
        if self.last_rect and self.last_rect == rect:
            return
        
        self.invalidate_rect()
        self.draw_outline((240, 34, 19), 2, rect)
        self.last_rect = rect

    def invalidate_rect(self, rect: Rect = None):
        if rect:
            rect = to_tuple(rect)
            win32gui.InvalidateRect(self.hwnd, rect, False)
            win32gui.UpdateWindow(self.hwnd)
        else:
            win32gui.InvalidateRect(self.hwnd, self.monitor, False)
            win32gui.UpdateWindow(self.hwnd)

    def prepare_countdown(self):
        self.countdown = 5
        self.countdown_hwnd = win32gui.CreateWindow(
                    'Static', '',
                    WS_POPUP,
                    0, 0, 100, 100,
                    self.window.winId(), None, self.hinst, None
                )
        self.dc = win32gui.GetDC(self.countdown_hwnd)
        font = CreateFontW(100, 100, 0, 0, FW_BOLD, 0, 0, 0, ANSI_CHARSET, OUT_DEVICE_PRECIS, CLIP_DEFAULT_PRECIS, DEFAULT_QUALITY, DEFAULT_PITCH, None)
        win32gui.SelectObject(self.dc, font)
        win32gui.SetWindowPos(
            self.countdown_hwnd, 
            HWND_TOPMOST, 
            0, 0, 100, 100, 
            SWP_NOACTIVATE | SWP_SHOWWINDOW)
        self.countdown_timer.start()
        
        
    
    def show_countdown(self):
        TextOut(self.dc, 0, 0, str(self.countdown), 1)

        self.countdown -= 1
        if self.countdown < 0:
            self.countdown_timer.stop()
            win32gui.ReleaseDC(self.countdown_hwnd, self.dc)
            win32gui.DestroyWindow(self.countdown_hwnd)
            self.start()

    def create_window(self):
        # brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 255))
        # wndcls = WNDCLASSEX()
        # wndcls.cbSize = sizeof(WNDCLASSEX)
        # wndcls.style = 0
        # wndcls.lpfnWndProc = WNDPROC(wnd_proc)
        # wndcls.cbClsExtra = 0
        # wndcls.cbWndExtra = 0
        # wndcls.hInstance = self.hinst
        # wndcls.hIcon = None
        # wndcls.hCursor = win32gui.LoadCursor(0, IDC_HAND)
        # wndcls.hbrBackground = int(brush)
        # wndcls.lpszMenuName = ''
        # wndcls.lpszClassName = 'Screen'
        # wndcls.hIconSm = None

        # RegisterClassEx(wndcls)
        # self.hwnd = CreateWindowEx(
        #     WS_EX_TOPMOST | WS_EX_LAYERED,
        #     'Screen',
        #     'Screen',
        #     WS_POPUP | WS_VISIBLE,
        #     *self.monitor,
        #     self.window.winId(), None,
        #     self.hinst, None
        # )

        # SetLayeredWindowAttributes(self.hwnd, 0, 75, LWA_ALPHA)
        

        self.hwnd = win32gui.CreateWindow(
            'Static', '',
            WS_VISIBLE | WS_POPUP,
            *self.monitor,
            self.window.winId(), None, self.hinst, None
        )
        origin_proc = GetWindowLongPtr(self.hwnd, GWL_WNDPROC)
        def new_proc(hwnd: HWND, uMsg: int, wParam: int, lParam: int) -> int:
            if uMsg == win32con.WM_MOUSEACTIVATE:
                return win32con.MA_NOACTIVATEANDEAT
            return win32gui.CallWindowProc(origin_proc, hwnd, uMsg, wParam, lParam)
        win32gui.SetWindowLong(self.hwnd, GWL_WNDPROC, WNDPROC(new_proc))
        win32gui.SetWindowLong(self.hwnd, GWL_EXSTYLE, WS_EX_TOPMOST | WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 75, LWA_ALPHA)
        win32gui.RegisterHotKey(self.hwnd, 1, 0x4000, 0x71) # F2
        win32gui.RegisterHotKey(self.hwnd, 2, 0x4000, 0x1B) # ESC
        win32gui.RegisterHotKey(self.hwnd, 3, 0x4000, 0x0D) # ENTER
        # brush = win32gui.CreateSolidBrush(win32api.RGB(255, 0, 0))
        # dc = win32gui.GetDC(self.hwnd)
        # win32gui.FillRect(dc, self.monitor, brush)
        self.block_input()

    def destroy_screen(self):
        UnregisterHotKey(self.hwnd, 1)
        UnregisterHotKey(self.hwnd, 2)
        UnregisterHotKey(self.hwnd, 3)
        win32gui.DestroyWindow(self.hwnd)
        self.hwnd = None

    def transfer_input(self):
        win32gui.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_HIDEWINDOW)
        # win32gui.SetWindowLong(self.hwnd, GWL_EXSTYLE, win32gui.GetWindowLong(self.hwnd, GWL_EXSTYLE) | WS_EX_TRANSPARENT)
        # win32gui.RedrawWindow(self.hwnd, None, None, RDW_INVALIDATE)

    def block_input(self):
        win32gui.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        # win32gui.SetWindowLong(self.hwnd, GWL_EXSTYLE, win32gui.GetWindowLong(self.hwnd, GWL_EXSTYLE) & (~WS_EX_TRANSPARENT))
        # win32gui.RedrawWindow(self.hwnd, None, None, RDW_INVALIDATE)

    def draw_outline(self, color: Tuple, thickness: int, rect: Rect):
        rect = to_tuple(rect)
        pen_handle = win32gui.CreatePen(PS_SOLID, thickness, win32api.RGB(*color))
        log_brush = LOGBRUSH()
        log_brush.lbStyle = BS_NULL
        brush_handle = CreateBrushIndirect(log_brush)
        dc = win32gui.CreateDC('DISPLAY', None, None)
        win32gui.SelectObject(dc, pen_handle)
        win32gui.SelectObject(dc, brush_handle)
        win32gui.Rectangle(dc, *rect)

        win32gui.DeleteObject(pen_handle)
        win32gui.DeleteObject(brush_handle)
        win32gui.DeleteDC(dc)

    def highlight(self, rect: Tuple):
        self.highlight_widget = QtWidgets.QWidget()
        self.highlight_widget.setWindowFlags(Qt.ToolTip)
        self.highlight_widget.setStyleSheet("background-color: rgb(49, 120, 192); border: 2px solid yellow")
        self.highlight_widget.setWindowOpacity(0.5)
        # self.highlight_widget.setGeometry(rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top)
        self.highlight_widget.show()
        win32gui.SetWindowPos(
            self.highlight_widget.winId(), 
            HWND_TOPMOST, 
            *rect,
            SWP_NOACTIVATE
            )

    def remove_highlight(self):
        if self.highlight_widget:
            self.highlight_widget.close()


class MainWindow(QtWidgets.QMainWindow):
    show_selector_signal = QtCore.Signal()
    delay_signal = QtCore.Signal()
    quit_signal = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.set_ui()
        self.screen_mgr = ScreenManager(self)
        # connect signals
        self.show_selector_signal.connect(self.show_selectors)
        self.delay_signal.connect(self.delay)
        self.quit_signal.connect(self.quit)

        self.checked_font = QtGui.QFont('Arial', italic=True)
        self.checked_font.setBold(True)
        self.unchecked_font = QtGui.QFont('Arial')

    def set_ui(self):
        self.setWindowTitle("UI Inspector")
        self.setFont(QtGui.QFont("Arial", 10))
        self.resize(800, 600)
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/magnifier.png")))

        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels([""])
        self.tree.header().hide()
        self.tree.setColumnWidth(0, self.tree.width())
        self.tree.setAutoScroll(False)
        self.tree.setExpandsOnDoubleClick(False)
        # self.tree.setUniformRowHeights(True)
        self.tree.itemExpanded.connect(self.show_children)
        self.tree.itemClicked.connect(self.show_properties)
        self.tree.itemDoubleClicked.connect(self.show_selectors)

        self.root_item = UIATreeItem(auto.GetRootControl(), self.tree, "Desktop")
        self.show_children(self.root_item)
        self.root_item.setExpanded(True)

        # create first groupbox
        self.groupbox = QtWidgets.QGroupBox("Visual Tree")
        self.groupbox.setLayout(QtWidgets.QVBoxLayout())
        self.groupbox.layout().addWidget(self.tree)

        # create list widget with check box for selectors
        self.selector_list = QtWidgets.QListWidget()
        self.selector_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.selector_list.itemChanged.connect(self.on_selectors_changed)

        # create text area
        self.selector_code_area = QtWidgets.QTextEdit()
        self.selector_code_area.setReadOnly(True)
        self.selector_code_area.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.selector_code_area.setFont(QtGui.QFont('Arial', 10))
        self.selector_code_area.setTextColor(QtGui.QColor(0, 0, 255))

        self.py_tab = QtWidgets.QWidget()
        self.py_tab.setLayout(QtWidgets.QHBoxLayout())
        self.py_tab.layout().addWidget(self.selector_code_area)

        self.copy_btn = QtWidgets.QPushButton(QtGui.QIcon(QtGui.QPixmap(":/icons/copy.png")), '')
        self.copy_btn.setIconSize(QtCore.QSize(16, 16))
        self.copy_btn.setFixedSize(16, 16)
        self.copy_btn.setVisible(False)
        self.copy_btn.clicked.connect(self.copy)

        btn_widget = QtWidgets.QWidget()
        btn_widget.setLayout(QtWidgets.QVBoxLayout())
        btn_widget.layout().setAlignment(Qt.AlignTop)
        btn_widget.layout().addWidget(self.copy_btn)
        self.py_tab.layout().addWidget(btn_widget)

        self.language_tabs = QtWidgets.QTabWidget()
        self.language_tabs.addTab(self.py_tab, 'Generated Code')
        # self.language_tabs.setStyleSheet("background: rgb(242, 242, 242);")

        # create second groupbox
        self.groupbox2 = QtWidgets.QGroupBox("Selectors")
        self.groupbox2.setLayout(QtWidgets.QVBoxLayout())
        self.groupbox2.layout().addWidget(self.selector_list)
        self.groupbox2.layout().addWidget(self.language_tabs)

        # create list widget for properties
        self.property_table = QtWidgets.QTableView()
        self.property_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
        header = self.property_table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
    
        # create third groupbox
        self.groupbox3 = QtWidgets.QGroupBox("Properties")
        self.groupbox3.setLayout(QtWidgets.QVBoxLayout())
        self.groupbox3.layout().addWidget(self.property_table)

        # create splitview
        self.split_view = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.split_view.setContentsMargins(0, 5, 0, 0)
        self.split_view.addWidget(self.groupbox)
        self.split_view.addWidget(self.groupbox2)
        self.split_view.addWidget(self.groupbox3)
        
        self.setCentralWidget(self.split_view)

        # create toolbar
        self.toolbar = QtWidgets.QToolBar()
        self.addToolBar(QtCore.Qt.LeftToolBarArea, self.toolbar)
        self.toolbar.setIconSize(QtCore.QSize(20, 20))
        self.toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        # set toolbar background color
        self.toolbar.setStyleSheet("QToolBar { background: rgba(171, 240, 173, 0.75); spacing: 10px}")

        refresh_action = QtGui.QAction(QtGui.QIcon(QtGui.QPixmap(":/icons/refresh.png")), "Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh)
        self.toolbar.addAction(refresh_action)

        indicate_action = QtGui.QAction(QtGui.QIcon(QtGui.QPixmap(":/icons/locate.png")), "Indicate Element", self)
        indicate_action.setShortcut("Ctrl+I")
        indicate_action.triggered.connect(self.indicate_element)
        self.toolbar.addAction(indicate_action)

        self.highlight_action = QtGui.QAction(QtGui.QIcon(QtGui.QPixmap(":/icons/highlight.png")), "Highlight Element", self)
        self.highlight_action.setShortcut("Ctrl+H")
        self.highlight_action.triggered.connect(self.highlight_element)
        self.highlight_action.setCheckable(True)
        self.highlight_action.setEnabled(False)
        self.toolbar.addAction(self.highlight_action)
        self.toolbar.addSeparator()

        # options_btn = QtWidgets.QToolButton()
        # options_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        # options_btn.setText("Options")
        # options_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/options.png")))
        # options_btn.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        # options_menu = QtWidgets.QMenu(options_btn)

        self.jab_action = QtGui.QAction("JAB", self)
        self.jab_action.setCheckable(True)
        self.jab_action.setChecked(True)

        self.uia_action = QtGui.QAction("UIA", self)
        self.uia_action.setCheckable(True)
        self.uia_action.setChecked(True)

        exit_action = QtGui.QAction('Exit', self)
        exit_action.triggered.connect(self.close)

        about_action = QtGui.QAction('About', self)
        about_action.triggered.connect(self.show_detail)

        # set menu
        menu = self.menuBar()
        file_menu = menu.addMenu('File')
        tools_menu = menu.addMenu('Tools')
        help_menu = menu.addMenu('Help')

        file_menu.addAction(exit_action)
        tools_menu.addActions([refresh_action, indicate_action, self.highlight_action])
        option_menu = tools_menu.addMenu(QtGui.QIcon(QtGui.QPixmap(":/icons/options.png")), 'Options')
        option_menu.addActions([self.jab_action, self.uia_action])
        help_menu.addAction(about_action)

        menu.setStyleSheet("background: rgba(171, 240, 173, 0.75);")

        
        # set statusbar
        self.statusbar = QtWidgets.QStatusBar()
        self.uia_label = QtWidgets.QLabel('uiautomation')
        self.jab_label = QtWidgets.QLabel('java access bridge')
        self.setStatusBar(self.statusbar)

    def minimize(self):
        """
        Minimize main window
        """
        win32gui.ShowWindow(self.winId(), SW_MINIMIZE)

    def restore(self):
        """
        Restore main window
        """
        win32gui.ShowWindow(self.winId(), SW_RESTORE)

    def copy(self):
        self.copy_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/check.png")))
        self.selector_code_area.selectAll()
        self.selector_code_area.copy()
        QtCore.QTimer.singleShot(3000, lambda : self.copy_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(":/icons/copy.png"))))

    def show_detail(self):
        info = f"""
        Version: {VERSION}
        Author: {AUTHOR}
        Contact: {MAIL}
        """
        QtWidgets.QMessageBox.information(self, 'UI Inspector', info)

    def show_error(self, message: str):
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QHBoxLayout())
        label = QtWidgets.QLabel(message)
        label.setStyleSheet("color: red;")
        btn = QtWidgets.QPushButton(QtGui.QIcon(QtGui.QPixmap(":/icons/close.png")), '')
        btn.setFixedSize(16, 16)
        btn.setIconSize(QtCore.QSize(16, 16))
        btn.clicked.connect(lambda : self.statusbar.removeWidget(widget))
        widget.layout().addWidget(label)
        widget.layout().addWidget(btn)
        self.statusbar.addWidget(widget)

    # manage screen 'delay' and 'quit' event
    def delay(self):
        self.screen_mgr.close()
        self.screen_mgr.timer.stop()
        self.screen_mgr.invalidate_rect()
        self.screen_mgr.transfer_input()
        # QtCore.QTimer.singleShot(5000, self.screen_mgr.start)
        self.screen_mgr.prepare_countdown()

    def quit(self):
        self.screen_mgr.close()
        self.screen_mgr.timer.stop()
        self.screen_mgr.destroy_screen()
        self.restore()

    def refresh(self):
        # remove all items from tree
        self.tree.clear()
        self.selector_list.clear()
        self.selector_code_area.clear()
        self.copy_btn.setVisible(False)
        self.property_table.setModel(None)
        self.highlight_action.setChecked(False)
        self.highlight_action.setEnabled(False)
        self.root_item = UIATreeItem(auto.GetRootControl(), self.tree, "Desktop")
        self.show_children(self.root_item)
        self.root_item.setExpanded(True)

    @QtCore.Slot(UITreeItem)
    def show_children(self, parent: UITreeItem) -> None:
        if parent.childCount() > 0:
            return
        # java control
        if isinstance(parent, JABTreeItem):
            for child in parent.control._generate_childs_from_element():
                child_item = JABTreeItem(child, parent)
                child_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        else:
            parent = cast(UIATreeItem, parent)
            for child in parent.control.GetChildren():
                if child.IsTopLevel():
                    try:
                        java_window = JDriver(hwnd = child.NativeWindowHandle)
                    except (FileNotFoundError, RuntimeError):
                        child_item = UIATreeItem(child, parent, child.Name)
                    else:
                        child_item = JABTreeItem(java_window._root_element, parent, java_window._root_element.name)
                else:
                    child_item = UIATreeItem(child, parent)
                child_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        if parent.childCount() <= 0:
            parent.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)

    @QtCore.Slot(UITreeItem)
    def show_properties(self, item: UITreeItem) -> None:
        try:
            item.update_property_table(self.property_table)

        except (comtypes.COMError, JABException, RuntimeError):
            # show a warning message
            QtWidgets.QMessageBox.warning(self, "Warning", "This element is unavailable now.")
            self.refresh()

    def get_control_from_cursor(self):
        x, y = win32gui.GetCursorPos()
        hwnd = win32gui.WindowFromPoint((x, y))
        hwnd = GetAncestor(hwnd, GA_ROOT)
        try:
            jdriver = JDriver(hwnd = hwnd)
        except (FileNotFoundError, RuntimeError):
            control = auto.ControlFromPoint(x, y)
        else:
            control = jdriver.get_accessible_context_at(x, y)

        return control

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def on_selectors_changed(self, item: QtWidgets.QListWidgetItem):
        if item.text().startswith('<java'):
            JABSelectorHelper().generate_code_from_selectors(self)
        else:
            UIASelectorHelper().generate_code_from_selectors(self)


    @QtCore.Slot(UITreeItem)
    def show_selectors(self, item: UITreeItem = None):
        """
        show selectors in list widget
        """
        if not item:
            self.screen_mgr.timer.stop()
            self.screen_mgr.destroy_screen()
        try:
            control = item.control if item else self.get_control_from_cursor()
            if isinstance(control, Control):
                selector_helper = UIASelectorHelper()
            elif isinstance(control, JElement):
                selector_helper = JABSelectorHelper()
            else:
                raise RuntimeError('Cannot recognize current window.')

            selector_helper.show_selectors_from_control(control, self)
            
        except Exception as e:
            self.statusbar.showMessage(str(e), 5000)
            # self.show_error(str(e))
        else:
            self.highlight_action.setEnabled(True)
        # restore main window
        if not item:
            self.restore()

    def indicate_element(self):
        # make window minimized
        self.minimize()
        self.screen_mgr.start()

    def highlight_element(self):

        if (row:=self.selector_list.item(0).text()).startswith('<java'):
            depth = 1
            _, attributes = JABSelectorHelper.parse_selector(row)
            try:
                jdriver = JDriver(attributes['name'], timeout=0)
                levels = []
                for i in range(1, self.selector_list.count()):
                    item = self.selector_list.item(i)
                    if item.checkState() == QtCore.Qt.Checked:
                        _, attributes = JABSelectorHelper.parse_selector(item.text())
                        attributes['depth'], depth = attributes['depth'] - depth, attributes['depth']
                        levels.append(dict(**attributes))
                if JElement.exists(jdriver.root_element, levels, 0):
                    bounds = jdriver.root_element.find_element_by_levels(levels, timeout=0).bounds
                    p1 = POINT(bounds['x'], bounds['y'])
                    LogicalToPhysicalPointForPerMonitorDPI(jdriver.hwnd, byref(p1))

                    p2 = POINT(bounds['x'] + bounds['width'], bounds['y'] + bounds['height'])
                    LogicalToPhysicalPointForPerMonitorDPI(jdriver.hwnd, byref(p2))
                    rect = (p1.x, p1.y, p2.x-p1.x, p2.y-p1.y)

                    if self.highlight_action.isChecked():
                        self.screen_mgr.highlight(rect)
                    else:
                        self.screen_mgr.remove_highlight()
                else:
                    self.highlight_action.setChecked(False)
                    self.highlight_action.setEnabled(False)
            except Exception as e:
                self.statusbar.showMessage(str(e), 5000)
                self.highlight_action.setChecked(False)
        else:
            depth = 0
            control: Control = auto
            for i in range(self.selector_list.count()):
                item = self.selector_list.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    control_type, attributes = UIASelectorHelper.parse_selector(item.text())
                    attributes['Depth'], depth = attributes['Depth'] - depth, attributes['Depth']
                    control = getattr(control, control_type)(**attributes)
            try:
                if control.Exists(0, printIfNotExist=False):
                    rect = control.BoundingRectangle
                    rect = (rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top)
                    if self.highlight_action.isChecked():
                        self.screen_mgr.highlight(rect)
                    else:
                        self.screen_mgr.remove_highlight()
                else:
                    self.highlight_action.setChecked(False)
                    self.highlight_action.setEnabled(False)
            except Exception as e:
                self.statusbar.showMessage(str(e), 5000)
                self.highlight_action.setChecked(False)
            

if __name__ == "__main__":
    app = QtWidgets.QApplication()

    window = MainWindow()
    window.show()

    with open('uiinspector/style.qss', 'r') as f:
        _style = f.read()
        app.setStyleSheet(_style)

    sys.exit(app.exec())