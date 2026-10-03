from offsets import *
from multiprocessing import Process
import asyncio, time, pymem, pymem.process
from src import fov, antiflash, glow, entity, esp

_esp: bool = True
_fov: bool = True
_antiflash: bool = False
_glow: bool = True

hooks = {}

# then use hooks["name"].join()
def createHook(hookName: str, hookLink, hookArgs: tuple = ()):
    process = Process(target=hookLink, args=hookArgs)
    process.start()

    hooks[hookName] = process

if __name__ == "__main__":
    if _fov:
            fov.setFOV(120)
    
    if _glow:
        while True:
            for pawn in entity.init_entity_list():
                glow.glow_entity(entity_pawn_addr=pawn)

    if _esp:
        esp.main()