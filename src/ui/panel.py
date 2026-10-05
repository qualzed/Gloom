import glfw
import imgui
import OpenGL.GL as gl
import win32con
import win32gui
import ctypes
from imgui.integrations.glfw import GlfwRenderer
from offsets import *
from src import aim, esp, crosshair
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

X, Y, W, H = game_rect()

def rgba(r, g, b, a=1.0):
     return imgui.get_color_u32_rgba(r, g, b, a)

def isPlanted():
     BombIsPlanted: bool = False

     try:
          PlantedC4 = pm.read_longlong(client + dwPlantedC4)
          BombIsPlanted = pm.read_bool(PlantedC4 + m_bBombTicking)
     except Exception:
          pass

     return BombIsPlanted

def bombExplosionTime():
     explosionTime: float = 0.0

     try:
          PlantedC4 = pm.read_longlong(client + dwPlantedC4)
          globalVars = pm.read_longlong(client + dwGlobalVars)
          explosionTime = pm.read_float(PlantedC4 + m_flC4Blow) - pm.read_float(globalVars + 0x30)
     except Exception:
          pass

     return explosionTime

def returnBombSite(): # 0 - A Plant, 1 - B Plant
     site: str = None

     try:
          PlantedC4 = pm.read_longlong(client + dwPlantedC4)
          bombPlant = pm.read_int(PlantedC4 + m_nBombSite)
          match bombPlant:
               case 0:
                    return "( A )"
               case 1:
                    return "( B )"
     except Exception:
          pass

     return ""

def isBeingDefused():
     status = False

     try:
          PlantedC4 = pm.read_longlong(client + dwPlantedC4)
          status = pm.read_bool(PlantedC4 + m_bBeingDefused)
     except Exception:
          pass

     return status

def get_text_size(text: str):
     tw, th = imgui.calc_text_size(text)
     return tw + 10, th + 10

def draw_panel(dl, x, y, w, h):
     border = 15.0

     # bg
     dl.add_rect_filled(
          x, y,
          x + w, y + h,
          rgba(0.04, 0.04, 0.05, 0.90),
          border
     )

     # border
     dl.add_rect(
          x, y,
          x + w, y + h,
          rgba(1.0, 1.0, 1.0, 0.15),
          border,
          thickness=1.0
     )

     status = None
     if isPlanted():
          status = "planted"
          string = f"Time until explosion: {bombExplosionTime():.1f}"
          dl.add_text( # static text
               x + 10,
               y + get_text_size(string)[1],
               rgba(1.0, 1.0, 1.0, 1.0),
               string
          )
     else:
          status = "not planted"

     if isBeingDefused():
          dl.add_text( # static text
               x + 65 + get_text_size("BOMB IS BEING DEFUSED")[0],
               y + 5,
               rgba(1.0, 0.0, 0.0, 1.0),
               f"BOMB IS BEING DEFUSED"
          )

     dl.add_text( # static text
          x + 10,
          y + 5,
          rgba(1.0, 1.0, 1.0, 1.0),
          f"Bomb status: {status} {returnBombSite()}"
     )

     dl.add_text( # static text
          x + w - get_text_size("AIM")[1] - 10,
          y + 5,
          rgba(0.0, 1.0, 0.0, 1.0) if aim.enabled != False else rgba(1.0, 0.0, 0.0, 1.0),
          "AIM"
     )

def main():
     if not glfw.init():
          exit("Could not initialize OpenGL context")

     global X, Y, W, H

     glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
     glfw.window_hint(glfw.DECORATED, glfw.FALSE)

     window = glfw.create_window(W, H, "ESP", None, None)

     if not window:
          glfw.terminate()
          exit("Could not create window")

     hwnd = glfw.get_win32_window(window)

     win32gui.SetWindowLong(
          hwnd,
          win32con.GWL_EXSTYLE,
          win32con.WS_EX_TRANSPARENT |
          win32con.WS_EX_LAYERED
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

          # =========================
          # panel
          # =========================

          panel_w = 700
          panel_h = 40

          panel_x = (W - panel_w) / 2
          panel_y = H - panel_h - 100

          draw_panel(
               imgui.get_window_draw_list(),
               panel_x,
               panel_y,
               panel_w,
               panel_h
          )

          crosshair.drawCrosshair(imgui.get_window_draw_list())
          if aim.enabled:
               crosshair.drawFOV(imgui.get_window_draw_list(), H * aim.RADIUS)

          if _esp:
               esp.draw_frame(imgui.get_window_draw_list())

          # =========================

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