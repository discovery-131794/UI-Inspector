from .structures import *
from typing import Pattern, Union
from ctypes.wintypes import ATOM, BYTE, COLORREF, HANDLE, HDC, HFONT, HMENU, HWND, DWORD, LPDWORD, LPPOINT, LPRECT, LPVOID, LPWSTR, PDWORD
import win32gui, win32com.client, win32api, win32con

# windows gdi api
CreateBrushIndirect = windll.gdi32.CreateBrushIndirect
CreateBrushIndirect.argtypes = [POINTER(LOGBRUSH)]
CreateBrushIndirect.restype = HBRUSH

CreateFontW = windll.gdi32.CreateFontW
CreateFontW.argtypes = [c_int, c_int, c_int, c_int, c_int, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCWSTR]
CreateFontW.restype = HFONT

# text output
TextOut = windll.gdi32.TextOutW
TextOut.argtypes = [HDC, c_int, c_int, LPCWSTR, c_int]
TextOut.restype = c_bool

ExtTextOut = windll.gdi32.ExtTextOutW
ExtTextOut.argtypes = [HDC, c_int, c_int, c_uint, LPRECT, LPCWSTR, c_uint, POINTER(c_int)]
ExtTextOut.restype = c_bool

DrawTextEx = windll.user32.DrawTextExW
DrawTextEx.argtypes = [HDC, LPWSTR, c_int, LPRECT, c_uint, LPDRAWTEXTPARAMS]
DrawTextEx.restype = c_int

BlockInput = windll.user32.BlockInput
BlockInput.argtypes = [c_bool]
BlockInput.restype = c_bool

SwitchToThisWindow = windll.user32.SwitchToThisWindow
SwitchToThisWindow.argtypes = [HWND, c_bool]

SetFocus = windll.user32.SetFocus
SetFocus.argtypes = [HWND]
SetFocus.restype = HWND

AttachThreadInput = windll.user32.AttachThreadInput
AttachThreadInput.argtypes = [DWORD, DWORD, c_bool]
AttachThreadInput.restype = c_bool

GetWindowThreadProcessId = windll.user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [HWND, LPDWORD]
GetWindowThreadProcessId.restype = DWORD

def get_foreground_window() -> HWND:
    return win32gui.GetForegroundWindow()

def switch_to_this_window(hwnd: HWND):
    if get_foreground_window() == hwnd:
        return
    SwitchToThisWindow(hwnd, True)

def set_window_foreground(hwnd: HWND):
    if get_foreground_window() == hwnd:
        return 
    win32com.client.Dispatch("WScript.Shell").SendKeys(' ')
    win32gui.SetForegroundWindow(hwnd)

def set_window_focus(hwnd: HWND):
    c_id = win32api.GetCurrentThreadId()
    w_id = GetWindowThreadProcessId(hwnd, None)
    AttachThreadInput(c_id, w_id, True)
    # win32gui.SetFocus(hwnd)
    SetFocus(hwnd)
    AttachThreadInput(c_id, w_id, False)

def set_window_active(hwnd: HWND):
    c_id = win32api.GetCurrentThreadId()
    w_id = GetWindowThreadProcessId(hwnd, None)
    AttachThreadInput(c_id, w_id, True)
    win32gui.SetActiveWindow(hwnd)
    AttachThreadInput(c_id, w_id, False)

def bring_window_to_top(hwnd: HWND):
    c_id = win32api.GetCurrentThreadId()
    w_id = GetWindowThreadProcessId(hwnd, None)
    AttachThreadInput(c_id, w_id, True)
    win32gui.BringWindowToTop(hwnd)
    AttachThreadInput(c_id, w_id, False)

def get_window_from_title(pattern: Union[str, Pattern]) -> HWND:
    hwnds = []
    def enum_window(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if (
            isinstance(pattern, str) and pattern == title
            or isinstance(pattern, Pattern) and pattern.match(title)
        ):
            hwnds.append(hwnd)
    win32gui.EnumWindows(enum_window, None)
    return hwnds[0] if hwnds else None


# callback function
def wnd_proc(hwnd: HWND, uMsg: int, wParam: int, lParam: int) -> int:
    if uMsg == win32con.WM_MOUSEACTIVATE:
        return win32con.MA_NOACTIVATE
    return win32gui.DefWindowProc(hwnd, uMsg, wParam, lParam)

RegisterClassEx = windll.user32.RegisterClassExW
RegisterClassEx.argtypes = [POINTER(WNDCLASSEX)]
RegisterClassEx.restype = ATOM

CreateWindowEx = windll.user32.CreateWindowExW
CreateWindowEx.argtypes = [DWORD, LPCWSTR, LPCWSTR, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU, HINSTANCE, LPVOID]
CreateWindowEx.restype = HWND

SetLayeredWindowAttributes = windll.user32.SetLayeredWindowAttributes
SetLayeredWindowAttributes.argtypes = [HWND, COLORREF, BYTE, DWORD]
SetLayeredWindowAttributes.restype = c_bool

GetClassInfoEx = windll.user32.GetClassInfoExW
GetClassInfoEx.argtypes = [HINSTANCE, LPCWSTR, POINTER(WNDCLASSEX)]
GetClassInfoEx.restype = c_bool

CallWindowProc = windll.user32.CallWindowProcW
CallWindowProc.argtypes = [WNDPROC, HWND, c_uint, WPARAM, LPARAM]
CallWindowProc.restype = LRESULT

GetWindowLongPtr = windll.user32.GetWindowLongPtrW
GetWindowLongPtr.argtypes = [HWND, c_int]
GetWindowLongPtr.restype = LONG_PTR

UnregisterHotKey = windll.user32.UnregisterHotKey
UnregisterHotKey.argtypes = [HWND, c_int]
UnregisterHotKey.restype = c_bool


# message loop
GetMessage = windll.user32.GetMessageW
GetMessage.argtypes = [LPMSG, HWND, c_uint, c_uint]
GetMessage.restype = c_int

DispatchMessage = windll.user32.DispatchMessageW
DispatchMessage.argtypes = [LPMSG]
DispatchMessage.restype = LRESULT

SendMessage = windll.user32.SendMessageW
SendMessage.argtypes = [HWND, c_uint, WPARAM, LPARAM]
SendMessage.restype = LRESULT

SendMessageTimeout = windll.user32.SendMessageTimeoutW
SendMessageTimeout.argtypes = [HWND, c_uint, WPARAM, LPARAM, c_uint, c_uint, POINTER(ULONG_PTR)]
SendMessageTimeout.restype = LRESULT

# coordinates
MapWindowPoints = windll.user32.MapWindowPoints
MapWindowPoints.argtypes = [HWND, HWND, LPPOINT, c_uint]
MapWindowPoints.restype = c_int

# window
GetAncestor = windll.user32.GetAncestor
GetAncestor.argtypes = [HWND, c_int]
GetAncestor.restype = HWND


# DPI Awareness
GetProcessDpiAwareness = windll.shcore.GetProcessDpiAwareness
GetProcessDpiAwareness.argtypes = [HANDLE, POINTER(PROCESS_DPI_AWARENESS)]
GetProcessDpiAwareness.restype = HRESULT

GetDpiForWindow = windll.user32.GetDpiForWindow
GetDpiForWindow.argtypes = [HWND]
GetDpiForWindow.restype = c_uint

GetDpiForSystem = windll.user32.GetDpiForSystem
GetDpiForSystem.argtypes = []
GetDpiForSystem.restype = c_uint

PhysicalToLogicalPointForPerMonitorDPI = windll.user32.PhysicalToLogicalPointForPerMonitorDPI
PhysicalToLogicalPointForPerMonitorDPI.argtypes = [HWND, LPPOINT]
PhysicalToLogicalPointForPerMonitorDPI.restype = c_bool

LogicalToPhysicalPointForPerMonitorDPI = windll.user32.LogicalToPhysicalPointForPerMonitorDPI
LogicalToPhysicalPointForPerMonitorDPI.argtypes = [HWND, LPPOINT]
LogicalToPhysicalPointForPerMonitorDPI.restype = c_bool
