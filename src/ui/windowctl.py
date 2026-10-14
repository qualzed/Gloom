import win32api
import win32con
import win32gui
import win32process

def set_clickable(hwnd, clickable):
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if clickable:
        style &= ~win32con.WS_EX_TRANSPARENT
    else:
        style |= win32con.WS_EX_TRANSPARENT

    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

def focus(hwnd):
    try:
        win32api.keybd_event(0x12, 0, 0, 0)
        current = win32api.GetCurrentThreadId()
        owner = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
        win32process.AttachThreadInput(current, owner, True)
        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)
        win32process.AttachThreadInput(current, owner, False)
        win32api.keybd_event(0x12, 0, 2, 0)
    except Exception:
        pass

def release_cursor():
    try:
        win32api.ClipCursor(None)
        for _ in range(10):
            if win32api.ShowCursor(True) >= 0:
                break
    except Exception:
        pass