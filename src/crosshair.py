import glfw
import imgui
import OpenGL.GL as gl
import win32con
import win32gui
import ctypes
from imgui.integrations.glfw import GlfwRenderer

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

def game_hwnd():
     return win32gui.FindWindow(None, "Counter-Strike 2")

def game_rect():
    hwnd = game_hwnd()
    if not hwnd:
        return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    _, _, w, h = win32gui.GetClientRect(hwnd)
    x, y = win32gui.ClientToScreen(hwnd, (0, 0))
    return x, y, w, h

X, Y, W, H = game_rect()

def rgba(r, g, b, a=1.0):
     return imgui.get_color_u32_rgba(r, g, b, a)

def drawFOV(dl, FOV):
     dl.add_rect(
          W / 2 - FOV, H / 2 - FOV,
          W / 2 + FOV, H / 2 + FOV,
          rgba(1.0, 1.0, 1.0, 0.2),
          360,
          thickness=3.0
     )

def drawCrosshair(dl):
     dl.add_rect_filled(
          W / 2 - 3.5, H / 2 - 3.5,
          W / 2 + 3.5, H / 2 + 3.5,
          rgba(0.04, 0.04, 0.05, 0.90),
          360.0
     )