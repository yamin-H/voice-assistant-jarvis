"""Low-level Windows helpers: find windows, move them, focus them, press keys."""
import ctypes
import subprocess
from ctypes import wintypes

try:  # make window coordinates match real screen pixels
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.IsIconic.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetForegroundWindow.restype = wintypes.HWND
dwmapi.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]

SW_MAXIMIZE, SW_MINIMIZE, SW_RESTORE = 3, 6, 9
SWP_NOZORDER, SWP_SHOWWINDOW = 0x0004, 0x0040
WM_CLOSE = 0x0010
GWL_EXSTYLE, WS_EX_TOOLWINDOW = -20, 0x80
DWMWA_CLOAKED = 14
SPI_GETWORKAREA = 0x0030

VK_VOLUME_MUTE, VK_VOLUME_DOWN, VK_VOLUME_UP = 0xAD, 0xAE, 0xAF
VK_MEDIA_NEXT, VK_MEDIA_PREV, VK_MEDIA_PLAY_PAUSE = 0xB0, 0xB1, 0xB3

IGNORED_TITLES = {"Program Manager"}

# Everyday names -> words that appear in window titles.
ALIASES = {
    "browser": ["google chrome", "microsoft edge", "firefox", "brave"],
    "chrome": ["google chrome"],
    "edge": ["microsoft edge"],
    "vs code": ["visual studio code"],
    "code": ["visual studio code"],
    "terminal": ["powershell", "command prompt", "terminal"],
}


def press_key(code, times=1):
    for _ in range(times):
        user32.keybd_event(code, 0, 0, 0)  # key down
        user32.keybd_event(code, 0, 2, 0)  # key up


def launch(command):
    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)


def list_windows():
    """Returns [(handle, title)] for the windows you can see, top one first."""
    found = []

    @EnumWindowsProc
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        cloaked = wintypes.DWORD(0)  # hidden windows (some Windows apps) count as "cloaked"
        dwmapi.DwmGetWindowAttribute(
            hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
        )
        if cloaked.value:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if buffer.value not in IGNORED_TITLES:
            found.append((hwnd, buffer.value))
        return True

    user32.EnumWindows(callback, 0)
    return found


def find_window(name):
    """Finds an open window by app name. Returns (handle, title) or None."""
    name = name.lower().strip()
    needles = ALIASES.get(name, [name])
    windows = list_windows()
    for hwnd, title in windows:  # first choice: the title ENDS with the name
        if any(title.lower().endswith(n) for n in needles):
            return hwnd, title
    for hwnd, title in windows:  # second choice: the title contains the name
        if any(n in title.lower() for n in needles):
            return hwnd, title
    return None


def foreground_window():
    return user32.GetForegroundWindow()


def title_of(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def work_area():
    """The usable screen area (without the taskbar): x, y, width, height."""
    rect = wintypes.RECT()
    user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def snap(hwnd, side):
    x, y, width, height = work_area()
    half = width // 2
    left, new_width = (x, half) if side == "left" else (x + half, width - half)
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, None, left, y, new_width, height, SWP_NOZORDER | SWP_SHOWWINDOW)


def focus(hwnd):
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    # Windows blocks programs from stealing focus. Tapping Alt first lets it through.
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)
    user32.SetForegroundWindow(hwnd)


def maximize(hwnd):
    user32.ShowWindow(hwnd, SW_MAXIMIZE)


def minimize(hwnd):
    user32.ShowWindow(hwnd, SW_MINIMIZE)


def close_window(hwnd):
    """Politely asks the window to close (apps still ask about unsaved work)."""
    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)


def show_desktop():
    user32.keybd_event(0x5B, 0, 0, 0)  # Windows key down
    user32.keybd_event(0x44, 0, 0, 0)  # D down
    user32.keybd_event(0x44, 0, 2, 0)
    user32.keybd_event(0x5B, 0, 2, 0)