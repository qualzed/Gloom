import ctypes
import math
import os
import struct
import time
import traceback
import glfw
import imgui
import OpenGL.GL as gl
import pymem
import pymem.process
import requests
import win32con
import win32gui
from imgui.integrations.glfw import GlfwRenderer
from src import entity
from offsets import *

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


# --- attach ---
print("Waiting for cs2.exe")
while True:
    time.sleep(1)
    try:
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        break
    except Exception:
        pass

time.sleep(1)
os.system("cls")
print("ESP loaded")


# --- helpers ---
def clamp(v):
    return 0.0 if v < 0 else 1.0 if v > 1 else v

def lerp(a, b, t):
    return a + (b - a) * t

def approach(cur, target, speed, dt):
    return target + (cur - target) * math.exp(-speed * dt)

def rgba(r, g, b, a=1.0):
    return imgui.get_color_u32_rgba(r, g, b, a)

def hp_color(f):
    if f < 0.5:
        return rgba(1.0, lerp(0.22, 0.82, f * 2), lerp(0.22, 0.20, f * 2))
    k = (f - 0.5) * 2
    return rgba(lerp(1.0, 0.25, k), lerp(0.82, 0.95, k), lerp(0.20, 0.40, k))

def w2s(m, x, y, z):
    w = m[12] * x + m[13] * y + m[14] * z + m[15]
    if w < 0.001:
        return None
    return (W / 2 + W / 2 * (m[0] * x + m[1] * y + m[2] * z + m[3]) / w,
            H / 2 - H / 2 * (m[4] * x + m[5] * y + m[6] * z + m[7]) / w)


# --- state ---
anim = {}
last_time = time.perf_counter()
reported = set()


# --- player ---
def draw_player(dl, pawn, matrix, local_team, dt):
    # read
    hp = pm.read_int(pawn + m_iHealth)
    if hp <= 0 or pm.read_uchar(pawn + m_lifeState):
        return False

    armor = max(0, pm.read_int(pawn + m_ArmorValue))
    team = pm.read_int(pawn + m_iTeamNum)

    # bones: 0 origin, 7 head
    scene = pm.read_longlong(pawn + m_pGameSceneNode)
    bones = pm.read_longlong(scene + m_modelState + 0x80)
    data = pm.read_bytes(bones, 8 * 0x20)
    ox, oy, oz = struct.unpack_from("3f", data, 0)
    head_z = struct.unpack_from("f", data, 7 * 0x20 + 8)[0] + 8

    # screen position
    top, bottom = w2s(matrix, ox, oy, head_z), w2s(matrix, ox, oy, oz)
    if not top or not bottom:
        return False

    h = bottom[1] - top[1]
    if h < 4 or h > H * 2:
        return False

    l, r = round(top[0] - h / 4), round(top[0] + h / 4)
    t, b = round(top[1]), round(bottom[1])
    if r < 0 or l > W or b < 0 or t > H:
        return False

    # animation
    hp_f, armor_f = clamp(hp / 100), clamp(armor / 100)
    st = anim.setdefault(pawn, [hp_f, hp_f, armor_f])
    st[0] = approach(st[0], hp_f, 10, dt)
    st[2] = approach(st[2], armor_f, 10, dt)
    st[1] = approach(max(st[1], st[0]), st[0], 2.5, dt)

    black, dark = rgba(0, 0, 0, 0.85), rgba(0.1, 0.1, 0.1, 0.9)

    # render: box
    rgb = (0.35, 0.80, 1.00) if team == local_team else (1.00, 0.35, 0.35)
    dl.add_rect_filled(l, t, r, b, rgba(*rgb, 0.07))
    cw, ch = max(4, (r - l) * 0.28), max(4, h * 0.18)
    segs = []
    for x, y, sx, sy in ((l, t, 1, 1), (r, t, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
        segs += [(x + .5, y + .5, x + .5 + sx * cw, y + .5), (x + .5, y + .5, x + .5, y + .5 + sy * ch)]
    for s in segs:
        dl.add_line(*s, black, 3.0)
    for s in segs:
        dl.add_line(*s, rgba(*rgb), 1.0)

    # name = pm.read_string(pawn + m_sSanitizedPlayerName)
    # dl.add_text(x1 - 3 - size.x, ty, rgba(1, 1, 1), name) # Nick

    # render: health bar
    x2 = l - 5
    x1 = x2 - 3
    fill_y = b - h * st[0]
    dl.add_rect_filled(x1 - 1, t - 1, x2 + 1, b + 1, black)
    dl.add_rect_filled(x1, t, x2, b, dark)
    dl.add_rect_filled(x1, b - h * st[1], x2, b, rgba(1, 1, 1, 0.45))
    dl.add_rect_filled(x1, fill_y, x2, b, hp_color(st[0]))
    if hp < 100:
        size = imgui.calc_text_size(str(hp))
        ty = min(max(fill_y - size.y / 2, t - 2), b - size.y + 2)
        dl.add_text(x1 - 2 - size.x, ty + 1, rgba(0, 0, 0, 0.9), str(hp))
        dl.add_text(x1 - 3 - size.x, ty, rgba(1, 1, 1), str(hp))

    # render: armor bar
    if armor > 0 or st[2] > 0.01:
        y1 = b + 4
        dl.add_rect_filled(l - 1, y1 - 1, r + 1, y1 + 4, black)
        dl.add_rect_filled(l, y1, r, y1 + 3, dark)
        dl.add_rect_filled(l, y1, l + (r - l) * st[2], y1 + 3, rgba(0.35, 0.65, 1.0))
    return True


# --- frame ---
def draw_frame(dl):
    global last_time
    now = time.perf_counter()
    dt, last_time = min(now - last_time, 0.1), now

    try:
        matrix = struct.unpack("16f", pm.read_bytes(client + dwViewMatrix, 64))
        local_team = pm.read_int(pm.read_longlong(client + dwLocalPlayerPawn) + m_iTeamNum)
    except Exception:
        return

    seen = set()
    for pawn in entity.init_entity_list():
        try:
            if draw_player(dl, pawn, matrix, local_team, dt):
                seen.add(pawn)
        except Exception:
            err = traceback.format_exc()
            if err not in reported:
                reported.add(err)
                print(err)

    for pawn in [p for p in anim if p not in seen]:
        del anim[pawn]


# --- window ---
def main():
    if not glfw.init():
        exit("Could not initialize OpenGL context")

    global X, Y, W, H

    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
    glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    window = glfw.create_window(W, H, "ESP", None, None)
    hwnd = glfw.get_win32_window(window)

    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, X, Y, W, H, win32con.SWP_NOACTIVATE)

    glfw.make_context_current(window)
    imgui.create_context()
    impl = GlfwRenderer(window)

    flags = (imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_SCROLLBAR
             | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BACKGROUND)

    # loop
    shown = True
    while not glfw.window_should_close(window):
        active = win32gui.GetForegroundWindow() == game_hwnd()
        if active != shown:
            shown = active
            (glfw.show_window if active else glfw.hide_window)(window)
        if not active:
            glfw.poll_events()
            time.sleep(0.05)
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
        draw_frame(imgui.get_window_draw_list())
        imgui.end()
        imgui.end_frame()

        gl.glClearColor(0, 0, 0, 0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == '__main__':
    main()