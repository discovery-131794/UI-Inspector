from ctypes import *
from ctypes.wintypes import DWORD, LPARAM, POINT, WPARAM, HWND, HINSTANCE, HICON, HBRUSH, LPCWSTR
import struct

LRESULT = LPARAM
HCURSOR = HICON

class LOGBRUSH(Structure):
    _fields_ = [
        ("lbStyle", c_uint),
        ("lbColor", c_ulong),
        ("lbHatch", c_long)
    ]

WNDPROC = CFUNCTYPE(LRESULT, HWND, c_uint, WPARAM, LPARAM)

if struct.calcsize('P') == 8:
    LONG_PTR = c_int64
    ULONG_PTR = c_uint64
else:
    LONG_PTR = c_long
    ULONG_PTR = c_ulong



class WNDCLASSEX(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('style', c_uint),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', c_int),
        ('cbWndExtra', c_int),
        ('hInstance', HINSTANCE),
        ('hIcon', HICON),
        ('hCursor', HCURSOR),
        ('hbrBackground', HBRUSH),
        ('lpszMenuName', LPCWSTR),
        ('lpszClassName', LPCWSTR),
        ('hIconSm', HICON)
    ]

class MSG(Structure):
    _fields_ = [
        ('hwnd', HWND),
        ('message', c_uint),
        ('wParam', WPARAM),
        ('lParam', LPARAM),
        ('time', DWORD),
        ('pt', POINT),
        ('lPrivate', DWORD)
    ]
LPMSG = POINTER(MSG)

# windows gdi structures
class DRAWTEXTPARAMS(Structure):
    """
    The DRAWTEXTPARAMS structure contains extended formatting options for DrawTextEx function.
    """
    _fields_ = [
        ('cbSize', c_uint),
        ('iTabLength', c_int),
        ('iLeftMargin', c_int),
        ('iRightMargin', c_int),
        ('uiLengthDrawn', c_uint)
    ]
LPDRAWTEXTPARAMS = POINTER(DRAWTEXTPARAMS)


class PROCESS_DPI_AWARENESS(c_int):
    PROCESS_DPI_UNAWARE = 0
    PROCESS_SYSTEM_DPI_AWARE = 1
    PROCESS_PER_MONITOR_DPI_AWARE = 2
