import ctypes
import math
import struct
import time
import win32api
import win32con
import win32gui
from offsets import *
from src import entity

HOLD_KEY = 0x06

ctypes.windll.user32.SetProcessDPIAware()


def get_game_size():
    hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
    if not hwnd or win32gui.GetForegroundWindow() != hwnd:
        return None
    _, _, width, height = win32gui.GetClientRect(hwnd)
    return width, height


def world_to_screen(m, x, y, z, width, height):
    w = m[12] * x + m[13] * y + m[14] * z + m[15]
    if w < 0.001:
        return None
    sx = width / 2 + width / 2 * (m[0] * x + m[1] * y + m[2] * z + m[3]) / w
    sy = height / 2 - height / 2 * (m[4] * x + m[5] * y + m[6] * z + m[7]) / w
    return sx, sy


def crosshair_on_head(matrix, pawn, width, height):
    scene = pm.read_longlong(pawn + m_pGameSceneNode)
    bones = pm.read_longlong(scene + m_modelState + 0x80)
    x, y, z = struct.unpack("3f", pm.read_bytes(bones + 7 * 0x20, 12))

    center = world_to_screen(matrix, x, y, z + 3, width, height)
    edge = world_to_screen(matrix, x, y, z + 8, width, height)
    if not center or not edge:
        return False

    radius = abs(center[1] - edge[1]) + 1
    distance = math.hypot(center[0] - width / 2, center[1] - height / 2)
    return distance <= radius


def click():
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def trigger():
    last_shot = 0.0

    while True:
        time.sleep(0.001)

        if not win32api.GetAsyncKeyState(HOLD_KEY) & 0x8000:
            continue

        size = get_game_size()
        if not size or time.perf_counter() - last_shot < 0.12:
            continue

        try:
            matrix = struct.unpack("16f", pm.read_bytes(client + dwViewMatrix, 64))
            for pawn in entity.init_entity_list():
                if crosshair_on_head(matrix, pawn, *size):
                    click()
                    last_shot = time.perf_counter()
                    break
        except Exception:
            continue