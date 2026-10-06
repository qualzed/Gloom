import ctypes
import glfw
import imgui
import OpenGL.GL as gl
import win32api, win32con, win32gui
from imgui.integrations.glfw import GlfwRenderer
from offsets import *
from src import aim, esp, crosshair, playerState
from src.ui import menu
from main import _esp, _aim, _antiflash, _antismoke, _glow, _fov, _trigger

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
          return "A" if site == 0 else "B" if site == 1 else ""
     except Exception:
          return ""

# def isBeingDefused():
#      try:
#           planted_c4 = pm.read_longlong(client + dwPlantedC4)
#           return pm.read_bool(planted_c4 + m_bBeingDefused)
#      except Exception:
#           return False

def get_text_size(text):
     tw, th = imgui.calc_text_size(text)
     return tw + 10, th + 10

def draw_functions_panel(dl, weight = None, height = None):
     x, y = 5, 3 # left upper corner
     step = 2

     features = [
          (_aim, "AIM"),
          (_esp, "ESP"),
          (_glow, "GLOW"),
          (_trigger, "TRIGGER"),
          (_fov, "FOV"),
          (_antismoke, "ANTISMOKE"),
          (_antiflash, "ANTIFLASH")
     ]

     for flag, name in features:
          if flag:
               dl.add_text(x, y, rgba(1.0, 1.0, 1.0, 1.0), name)
               x += get_text_size(name)[0] + step


def draw_bomb_panel(dl, weight = None, height = None):
     radius = 10.0
     w, h = 140, 80
     x, y = 20, (height / 2) - (h / 2)

     dl.add_rect_filled(x, y, x + w, y + h, rgba(0.02, 0.02, 0.03, 0.85), radius)
     dl.add_rect(x, y, x + w, y + h, rgba(1.0, 1.0, 1.0, 0.12), radius, thickness=1.0)

     tx, ty, step = x + 12, y + 10, -1

     dl.add_text(tx, ty, rgba(1.0, 1.0, 1.0, 1.0), "C4 PLANTED")
     ty += get_text_size("C4 PLANTED")[1] + step

     site_str = f"Site: {returnBombSite()}"
     dl.add_text(tx, ty, rgba(0.65, 0.65, 0.70, 1.0), site_str)
     ty += get_text_size(site_str)[1] + step

     timer_str = f"Explosion: {bombExplosionTime():.1f}s"
     dl.add_text(tx, ty, rgba(1.0, 0.35, 0.35, 1.0), timer_str)

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

          draw_functions_panel(imgui.get_window_draw_list(), W, H)
          if isPlanted():
               draw_bomb_panel(imgui.get_window_draw_list(), W, H)

          if win32api.GetAsyncKeyState(win32con.VK_INSERT) & 1:
               menu_open = not menu_open
          if menu_open:
               script_menu.draw(imgui.get_window_draw_list(), W, H)

          if playerState.IsInGame():
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