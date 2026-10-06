import ctypes
import glfw
import imgui
import OpenGL.GL as gl
import win32api, win32con, win32gui
from imgui.integrations.glfw import GlfwRenderer
from offsets import *
from src import aim, esp, crosshair
from src.ui import menu
from main import _esp

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

def rgba(r, g, b, a=1.0):
     return imgui.get_color_u32_rgba(r, g, b, a)

def isPlanted():
     try:
          planted_c4 = pm.read_longlong(client + dwPlantedC4)
          return pm.read_bool(planted_c4 + m_bBombTicking)
     except Exception:
          return False

def bombExplosionTime():
     try:
          planted_c4 = pm.read_longlong(client + dwPlantedC4)
          global_vars = pm.read_longlong(client + dwGlobalVars)
          return pm.read_float(planted_c4 + m_flC4Blow) - pm.read_float(global_vars + 0x30)
     except Exception:
          return 0.0

def returnBombSite():
     try:
          planted_c4 = pm.read_longlong(client + dwPlantedC4)
          site = pm.read_int(planted_c4 + m_nBombSite)
          return "( A )" if site == 0 else "( B )" if site == 1 else ""
     except Exception:
          return ""

def isBeingDefused():
     try:
          planted_c4 = pm.read_longlong(client + dwPlantedC4)
          return pm.read_bool(planted_c4 + m_bBeingDefused)
     except Exception:
          return False

def get_text_size(text):
     tw, th = imgui.calc_text_size(text)
     return tw + 10, th + 10

def draw_panel(dl, x, y, w, h):
     radius = 15.0

     dl.add_rect_filled(
          x, y, x + w, y + h,
          rgba(0.04, 0.04, 0.05, 0.90),
          radius
     )

     dl.add_rect(
          x, y, x + w, y + h,
          rgba(1.0, 1.0, 1.0, 0.15),
          radius,
          thickness=1.0
     )

     planted = isPlanted()
     status = "planted" if planted else "not planted"

     dl.add_text(
          x + 10,
          y + 5,
          rgba(1.0, 1.0, 1.0),
          f"Bomb status: {status} {returnBombSite()}"
     )

     if planted:
          text = f"Time until explosion: {bombExplosionTime():.1f}"
          dl.add_text(
               x + 10,
               y + get_text_size(text)[1],
               rgba(1.0, 1.0, 1.0),
               text
          )

     if isBeingDefused():
          dl.add_text(
               x + 65 + get_text_size("BOMB IS BEING DEFUSED")[0],
               y + 5,
               rgba(1.0, 0.0, 0.0),
               "BOMB IS BEING DEFUSED"
          )

     dl.add_text(
          x + w - get_text_size("AIM")[1] - 10,
          y + 5,
          rgba(0.0, 1.0, 0.0) if aim.enabled else rgba(1.0, 0.0, 0.0),
          "AIM"
     )

def main():
     global X, Y, W, H

     if not glfw.init():
          raise RuntimeError("Could not initialize OpenGL context")

     X, Y, W, H = game_rect()

     glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
     glfw.window_hint(glfw.DECORATED, glfw.FALSE)

     window = glfw.create_window(W, H, "ESP", None, None)
     if not window:
          glfw.terminate()
          raise RuntimeError("Could not create window")

     hwnd = glfw.get_win32_window(window)

     win32gui.SetWindowLong(
          hwnd,
          win32con.GWL_EXSTYLE,
          win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
     )

     win32gui.SetWindowPos(
          hwnd,
          win32con.HWND_TOPMOST,
          X, Y, W, H,
          win32con.SWP_NOACTIVATE
     )

     glfw.make_context_current(window)

     imgui.create_context()
     impl = GlfwRenderer(window)

     flags = (
          imgui.WINDOW_NO_TITLE_BAR |
          imgui.WINDOW_NO_RESIZE |
          imgui.WINDOW_NO_SCROLLBAR |
          imgui.WINDOW_NO_COLLAPSE |
          imgui.WINDOW_NO_BACKGROUND
     )

     script_menu = menu.Menu()
     menu_open = False
     shown = True

     while not glfw.window_should_close(window):
          active = win32gui.GetForegroundWindow() == game_hwnd()

          if active != shown:
               shown = active
               if active:
                    glfw.show_window(window)
               else:
                    glfw.hide_window(window)

          if not active:
               glfw.poll_events()
               continue

          rect = game_rect()

          if rect != (X, Y, W, H) and rect[2] > 0 and rect[3] > 0:
               X, Y, W, H = rect
               glfw.set_window_pos(window, X, Y)
               glfw.set_window_size(window, W, H)

          glfw.poll_events()
          impl.process_inputs()
          imgui.new_frame()

          imgui.set_next_window_size(W, H)
          imgui.set_next_window_position(0, 0)
          imgui.begin("overlay", flags=flags)

          panel_w, panel_h = 700, 40
          panel_x = (W - panel_w) / 2
          panel_y = H - panel_h - 100

          draw_panel(
               imgui.get_window_draw_list(),
               panel_x,
               panel_y,
               panel_w,
               panel_h
          )

          # if win32api.GetAsyncKeyState(win32con.VK_INSERT) & 1:
          #      menu_open = not menu_open
          # if menu_open:
          #      script_menu.draw(imgui.get_window_draw_list(), W, H)

          crosshair.drawCrosshair(imgui.get_window_draw_list())

          if aim.enabled:
               crosshair.drawFOV(imgui.get_window_draw_list(), H * aim.RADIUS)

          if _esp:
               esp.draw_frame(imgui.get_window_draw_list())

          imgui.end()
          imgui.end_frame()

          gl.glClearColor(0, 0, 0, 0)
          gl.glClear(gl.GL_COLOR_BUFFER_BIT)

          imgui.render()
          impl.render(imgui.get_draw_data())
          glfw.swap_buffers(window)

     impl.shutdown()
     glfw.terminate()

if __name__ == "__main__":
     main()