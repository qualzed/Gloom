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
from internal import crashlog

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
    except Exception as e:
        crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
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

def tint(rgb, k):
    return tuple(lerp(1.0, c, k) for c in rgb)

def draw_text(dl, x, y, text, color):
    dl.add_text(x + 1, y + 1, rgba(0, 0, 0, 0.6), text)
    dl.add_text(x, y, rgba(*color), text)

def w2s(m, x, y, z):
    w = m[12] * x + m[13] * y + m[14] * z + m[15]
    if w < 0.001:
        return None
    return (W / 2 + W / 2 * (m[0] * x + m[1] * y + m[2] * z + m[3]) / w,
            H / 2 - H / 2 * (m[4] * x + m[5] * y + m[6] * z + m[7]) / w)

# --- hp gradient (green top, red bottom) ---
GREEN, YELLOW, RED = (0.32, 0.92, 0.55), (1.00, 0.80, 0.28), (1.00, 0.28, 0.32)

def grad_rgb(f):
    f = clamp(f)
    if f < 0.5:
        return tuple(lerp(a, c, f * 2) for a, c in zip(GREEN, YELLOW))
    return tuple(lerp(a, c, (f - 0.5) * 2) for a, c in zip(YELLOW, RED))

def hp_bar(dl, x1, x2, t, b, fill_y, alpha):
    mid = (t + b) / 2
    for y0, y1 in ((t, mid), (mid, b)):
        top = max(y0, fill_y)
        if top >= y1:
            continue
        c_top = rgba(*grad_rgb((top - t) / (b - t)), alpha)
        c_bot = rgba(*grad_rgb((y1 - t) / (b - t)), alpha)
        dl.add_rect_filled_multicolor(x1, top, x2, y1, c_top, c_top, c_bot, c_bot)

# --- state ---
anim = {}
carry_cache = {}
last_time = time.perf_counter()
reported = set()

# --- skeleton (bone pairs) ---
SKELETON_LINKS = (
    (1, 3), (3, 4), (4, 23), (23, 6), (6, 7),
    (6, 9), (9, 10), (10, 11),
    (6, 13), (13, 14), (14, 15),
    (1, 17), (17, 18), (18, 19),
    (1, 20), (20, 21), (21, 22),
)
SKELETON_BONES = {i for link in SKELETON_LINKS for i in link}

# --- weapons / items ---
def safe_field(cls, name):
    try:
        return field(cls, name)
    except Exception as e:
        crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
        return None

m_pWeaponServices = field('C_BasePlayerPawn', 'm_pWeaponServices')
m_hActiveWeapon = field('CPlayer_WeaponServices', 'm_hActiveWeapon')
m_hMyWeapons = safe_field('CPlayer_WeaponServices', 'm_hMyWeapons')
m_pItemServices = safe_field('C_BasePlayerPawn', 'm_pItemServices')
m_bHasDefuser = safe_field('CCSPlayer_ItemServices', 'm_bHasDefuser')

C4_ID = 49

WEAPONS = {
    1: "Desert Eagle", 2: "Dual Berettas", 3: "Five-SeveN", 4: "Glock-18",
    7: "AK-47", 8: "AUG", 9: "AWP", 10: "FAMAS", 11: "G3SG1", 13: "Galil AR",
    14: "M249", 16: "M4A4", 17: "MAC-10", 19: "P90", 23: "MP5-SD", 24: "UMP-45",
    25: "XM1014", 26: "PP-Bizon", 27: "MAG-7", 28: "Negev", 29: "Sawed-Off",
    30: "Tec-9", 31: "Zeus x27", 32: "P2000", 33: "MP7", 34: "MP9", 35: "Nova",
    36: "P250", 38: "SCAR-20", 39: "SG 553", 40: "SSG 08", 42: "Knife",
    43: "Flashbang", 44: "HE Grenade", 45: "Smoke", 46: "Molotov", 47: "Decoy",
    48: "Incendiary", 49: "C4", 59: "Knife", 60: "M4A1-S", 61: "USP-S",
    63: "CZ75-Auto", 64: "R8 Revolver",
}

def entity_from_handle(handle):
    index = handle & 0x7FFF
    entity_list = pm.read_longlong(client + dwEntityList)
    entry = pm.read_longlong(entity_list + 0x8 * (index >> 9) + 0x10)
    return pm.read_longlong(entry + 0x70 * (index & 0x1FF))

def item_id(weapon):
    try:
        return pm.read_ushort(weapon + m_AttributeManager + m_Item + m_iItemDefinitionIndex)
    except Exception:
        return 0

def weapon_name(pawn):
    try:
        services = pm.read_longlong(pawn + m_pWeaponServices)
        handle = pm.read_int(services + m_hActiveWeapon) & 0xFFFFFFFF
        if not services or handle == 0xFFFFFFFF:
            return ""
        item = item_id(entity_from_handle(handle))
    except Exception:
        return ""

    return "Knife" if item >= 500 else WEAPONS.get(item, "")

# --- player ---
def draw_player(dl, pawn, matrix, local_team, dt):
    # read
    hp = pm.read_int(pawn + m_iHealth)
    if hp <= 0 or pm.read_uchar(pawn + m_lifeState):
        return False

    team = pm.read_int(pawn + m_iTeamNum)

    # bones: 0 origin, 7 head, rest skeleton
    scene = pm.read_longlong(pawn + m_pGameSceneNode)
    if not scene:
        return False
    bones = pm.read_longlong(scene + m_modelState + 0x80)
    if not bones:
        return False

    data = pm.read_bytes(bones, 24 * 0x20)
    ox, oy, oz = struct.unpack_from("3f", data, 0)
    hx, hy, hz = struct.unpack_from("3f", data, 7 * 0x20)
    head_z = hz + 8

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
    hp_f = clamp(hp / 100)
    st = anim.setdefault(pawn, [hp_f, hp_f])
    st[0] = approach(st[0], hp_f, 10, dt)
    st[1] = approach(max(st[1], st[0]), st[0], 2.5, dt)

    # colors
    rgb = (0.36, 0.78, 1.00) if team == local_team else (1.00, 0.30, 0.34)
    accent = rgba(*rgb, 0.95)
    glow = rgba(*rgb, 0.08)
    shade = rgba(0, 0, 0, 0.22)
    panel = rgba(0.05, 0.05, 0.06, 0.55)
    bone_rgb = tint(rgb, 0.45)

    # render: name
    name = entity.names.get(pawn, "")
    if name:
        tw = imgui.calc_text_size(name)
        draw_text(dl, round((l + r) / 2 - tw.x / 2), round(t - tw.y - 5), name, (1, 1, 1, 0.95))

    # render: box
    for i in range(8):
        y0, y1 = round(t + (b - t) * i / 8), round(t + (b - t) * (i + 1) / 8)
        dl.add_rect_filled(l, y0, r, y1, rgba(*rgb, 0.015 + 0.012 * i))

    cw, ch = max(4, (r - l) * 0.28), max(4, h * 0.16)
    segs = []
    for x, y, sx, sy in ((l, t, 1, 1), (r, t, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
        segs += [(x + .5, y + .5, x + .5 + sx * cw, y + .5), (x + .5, y + .5, x + .5, y + .5 + sy * ch)]
    for s in segs:
        dl.add_line(*s, shade, 3.0)
    for s in segs:
        dl.add_line(*s, glow, 5.0)
    for s in segs:
        dl.add_line(*s, accent, 1.0)

    # render: skeleton
    points = {i: w2s(matrix, *struct.unpack_from("3f", data, i * 0x20)) for i in SKELETON_BONES}
    links = [(points[i], points[j]) for i, j in SKELETON_LINKS if points[i] and points[j]]
    bone_shade, bone_col = rgba(0, 0, 0, 0.15), rgba(*bone_rgb, 0.55)
    for p1, p2 in links:
        dl.add_line(*p1, *p2, bone_shade, 2.0)
    for p1, p2 in links:
        dl.add_line(*p1, *p2, bone_col, 1.0)
    for i, point in points.items():
        if point and i != 7:
            dl.add_circle_filled(*point, 1.0, rgba(*bone_rgb, 0.7), 8)

    # render: head circle
    center, edge = w2s(matrix, hx, hy, hz + 3), w2s(matrix, hx, hy, hz + 8)
    if center and edge:
        radius = abs(center[1] - edge[1])
        dl.add_circle(*center, radius, rgba(*bone_rgb, 0.10), 24, 4.0)
        dl.add_circle(*center, radius, rgba(*bone_rgb, 0.85), 24, 1.0)

    # render: health bar
    x2 = l - 5
    x1 = x2 - 3
    fill_y = b - h * st[0]
    trail_y = b - h * st[1]
    dl.add_rect_filled(x1 - 1, t - 1, x2 + 1, b + 1, panel, 2.0)
    dl.add_rect_filled(x1, trail_y, x2, b, rgba(1, 1, 1, 0.30), 1.0)
    glow_rgb = grad_rgb((fill_y - t) / max(b - t, 1))
    dl.add_rect_filled(x1 - 1, fill_y, x2 + 1, b, rgba(*glow_rgb, 0.18), 2.0)
    hp_bar(dl, x1, x2, t, b, fill_y, 0.95)
    dl.add_line(x1, fill_y + .5, x2, fill_y + .5, rgba(1, 1, 1, 0.55), 1.0)
    # if hp < 100:
    #     size = imgui.calc_text_size(str(hp))
    #     ty = min(max(fill_y - size.y / 2, t - 2), b - size.y + 2)
    #     draw_text(dl, x1 - 3 - size.x, ty, str(hp), (*glow_rgb, 0.95))

    # render: weapon
    weapon = weapon_name(pawn)
    if weapon:
        tw = imgui.calc_text_size(weapon)
        draw_text(dl, round((l + r) / 2 - tw.x / 2), b + 5, weapon, (0.85, 0.87, 0.92, 0.9))
        
    return True

# --- frame ---
def draw_frame(dl):
    global last_time
    now = time.perf_counter()
    dt, last_time = min(now - last_time, 0.1), now

    try:
        matrix = struct.unpack("16f", pm.read_bytes(client + dwViewMatrix, 64))
        local_team = pm.read_int(pm.read_longlong(client + dwLocalPlayerPawn) + m_iTeamNum)
    except Exception as e:
        crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
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
    for pawn in [p for p in carry_cache if p not in seen]:
        del carry_cache[pawn]