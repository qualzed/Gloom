# Claude Code

from colorama import Fore
import math
import struct
import time
import win32api
import win32con
import win32gui
from offsets import *
from src import entity
from internal import crashlog

TOGGLE_KEY = 0x05
SMOOTH = 6.0
SENS = 1.0
RADIUS = 0.08 # No more 0.5
HEAD_BONE = 7
enabled = None

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

def head_position(pawn):
    scene = pm.read_longlong(pawn + m_pGameSceneNode)
    if not scene:
        return None

    bones = pm.read_longlong(scene + m_modelState + 0x80)
    if not bones:
        return None

    return struct.unpack("3f", pm.read_bytes(bones + HEAD_BONE * 0x20, 12))

def find_target(matrix, width, height):
    best, best_distance = None, height * RADIUS

    for pawn in entity.init_entity_list():
        head = head_position(pawn)
        
        if not head:
            continue

        x, y, z = head
        point = world_to_screen(matrix, x, y, z + 3, width, height)
        if not point:
            continue

        dx, dy = point[0] - width / 2, point[1] - height / 2
        distance = math.hypot(dx, dy)
        if distance < best_distance:
            best, best_distance = (dx, dy), distance

    return best

def move_mouse(dx, dy, height):
    scale = 3906 / (height * SENS) / SMOOTH
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, round(dx * scale), round(dy * scale), 0, 0)

def aim():
    global enabled
    enabled = False
    was_down = False

    while True:
        local_player = pm.read_longlong(client + dwLocalPlayerPawn)

        size = get_game_size()
        down = bool(win32api.GetAsyncKeyState(TOGGLE_KEY) & 0x8000)
        if down and not was_down and size:
            enabled = not enabled
        was_down = down

        if not enabled or not size:
            time.sleep(0.001)
            continue

        try:
            if pm.read_uchar(local_player + m_lifeState) != 0:
                continue
        except Exception as e:
            crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
            pass

        try:
            matrix = struct.unpack("16f", pm.read_bytes(client + dwViewMatrix, 64))
            target = find_target(matrix, *size)
            if target:
                move_mouse(*target, size[1])
        except Exception as e:
            crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
            continue

        time.sleep(0.0055)