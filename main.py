import time, threading, inspect, win32api, win32con, os
from src import fov, antiflash, glow, entity, trigger, aim, scanner, antismoke, bhop
from src.ui import panel
from internal import serializer, rpc

hooks = {}

def createHook(hookName: str, hookLink, hookArgs: tuple = ()):
    stop_event = threading.Event()
    
    sig = inspect.signature(hookLink)
    params = list(sig.parameters.values())
    
    provided_args_count = len(hookArgs)
    
    if len(params) > provided_args_count:
        actual_args = hookArgs + (stop_event,)
        has_stop_event = True
    else:
        actual_args = hookArgs
        has_stop_event = False

    thread = threading.Thread(target=hookLink, args=actual_args, name=hookName, daemon=True)
    thread.start()
    
    hooks[hookName] = {"thread": thread, "stop_event": stop_event if has_stop_event else None}
    return thread

def stopHook(hookName: str):
    hook_data = hooks.pop(hookName, None)
    if hook_data:
        if hook_data["stop_event"]:
            hook_data["stop_event"].set()
        
        thread = hook_data["thread"]
        if thread.is_alive():
            thread.join(timeout=0.2)

def hookExist(hookName):
    if hookName in hooks:
        return True
    return False

def stopAll():
    for hookName in list(hooks):
        stopHook(hookName)

def loopTermination(stop_event: threading.Event):
    while not stop_event.is_set():
        if win32api.GetAsyncKeyState(win32con.VK_END) & 1:
            stopAll()
            break
        time.sleep(0.01)

def loadHooks():
    if serializer._fov:
        createHook("fov", fov.setFOV, (120,))

    if serializer._antiflash:
        createHook("antiflash", antiflash.antiflash)

    if serializer._aim:
        createHook("aim", aim.aim)

    if serializer._trigger:
        createHook("trigger", trigger.trigger)

    if serializer._antismoke:
        createHook("antismoke", antismoke.nosmoke)

    if serializer._bhop:
        createHook("antismoke", bhop.bhop)

    if serializer._glow:
        createHook("glow", glow.glow)

if __name__ == "__main__":
    os.system("cls")
    serializer.ReadJSON()

    loadHooks()

    createHook("panel", panel.main)
    createHook("rpc", rpc.StartRPC)
    createHook("termination", loopTermination)

    try:
        while any(data["thread"].is_alive() for data in hooks.values()):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stopAll()