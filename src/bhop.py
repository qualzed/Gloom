import time
import requests
import win32api
import win32gui
from offsets import *

HOLD_KEY = 0x20  # space
JUMP_ON = 65537
JUMP_OFF = 256
FL_ONGROUND = 1

m_fFlags = field('C_BaseEntity', 'm_fFlags')

def game_active():
    hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
    return bool(hwnd) and win32gui.GetForegroundWindow() == hwnd

def jump_offset():
    value = offsets['client.dll'].get('dwForceJump')
    if value is not None:
        return value

    try:
        return requests.get(BASE_URL + 'buttons.json', timeout=5).json()['client.dll']['jump']
    except Exception:
        raise SystemExit("jump button offset not found")

def bhop():
    jump = client + jump_offset()

    while True:
        time.sleep(0.001)

        if not win32api.GetAsyncKeyState(HOLD_KEY) & 0x8000 or not game_active():
            continue

        try:
            pawn = pm.read_longlong(client + dwLocalPlayerPawn)
            if pm.read_int(pawn + m_fFlags) & FL_ONGROUND:
                pm.write_int(jump, JUMP_ON)
                time.sleep(0.02)
                pm.write_int(jump, JUMP_OFF)
        except Exception:
            continue