import time
from multiprocessing import Process
from src import fov, antiflash, glow, entity, esp, trigger, aim, person

_esp: bool = True
_fov: bool = False
_antiflash: bool = True
_glow: bool = False
_trigger: bool = True
_aim: bool = True
_person: bool = True

hooks = {}

def createHook(hookName: str, hookLink, hookArgs: tuple = ()):
    process = Process(target=hookLink, args=hookArgs, name=hookName, daemon=True)
    process.start()

    hooks[hookName] = process
    return process

def stopHook(hookName: str):
    process = hooks.pop(hookName, None)
    if process and process.is_alive():
        process.terminate()
        process.join()

def stopAll():
    for hookName in list(hooks):
        stopHook(hookName)

def glowLoop():
    while True:
        for pawn in entity.init_entity_list():
            glow.glow_entity(entity_pawn_addr=pawn)
        time.sleep(0.001)

if __name__ == "__main__":
    if _fov:
        createHook("fov", fov.setFOV, (90,))

    if _antiflash:
        createHook("antiflash", antiflash.antiflash)

    if _glow:
        createHook("glow", glowLoop)

    if _esp:
        createHook("esp", esp.main)

    if _aim:
        createHook("aim", aim.aim)

    if _trigger:
        createHook("trigger", trigger.trigger)

    try:
        while any(process.is_alive() for process in hooks.values()):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stopAll()