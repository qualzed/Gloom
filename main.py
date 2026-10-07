import time
import threading
import inspect
from src import fov, antiflash, glow, entity, trigger, aim, scanner, antismoke
from src.ui import panel
from internal import serializer

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

def stopAll():
    for hookName in list(hooks):
        stopHook(hookName)

def glowLoop(stop_event: threading.Event):
    while not stop_event.is_set():
        for pawn in entity.init_entity_list():
            glow.glow_entity(entity_pawn_addr=pawn)
        time.sleep(0.001)

if __name__ == "__main__":
    serializer.ReadJSON()

    if serializer._fov:
        createHook("fov", fov.setFOV, (120,))

    if serializer._antiflash:
        createHook("antiflash", antiflash.antiflash)

    if serializer._glow:
        createHook("glow", glowLoop)

    if serializer._aim:
        createHook("aim", aim.aim)

    if serializer._trigger:
        createHook("trigger", trigger.trigger)

    if serializer._antismoke:
        createHook("antismoke", antismoke.nosmoke)

    createHook("panel", panel.main)

    try:
        while any(data["thread"].is_alive() for data in hooks.values()):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stopAll()