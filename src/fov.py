from offsets import *
import pymem, time
from internal import crashlog

localFOV = 90 # default fov value

def getCameraAndPawn():
    try:
        _dwLocalPlayerPawn = pm.read_longlong(client + dwLocalPlayerPawn)
        cameraServices = pm.read_longlong(_dwLocalPlayerPawn + m_pCameraServices)
    except Exception as e:
        crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
        pass
    
    return cameraServices, _dwLocalPlayerPawn

def returnFOV():
    fov = pm.read_uint(getCameraAndPawn()[0] + m_iFOV)
    return fov

def setFOV(fov: int, retry: bool = False):
    while 1:
        if pm.read_bool(getCameraAndPawn()[1] + m_bIsScoped):
            continue

        pm.write_uint(getCameraAndPawn()[0] + m_iFOV, fov)