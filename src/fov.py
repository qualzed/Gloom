from offsets import *
import pymem, time

localFOV = 90 # default fov value
_dwLocalPlayerPawn = pm.read_longlong(client + dwLocalPlayerPawn)
cameraServices = pm.read_longlong(_dwLocalPlayerPawn + m_pCameraServices)

def returnFOV():
    fov = pm.read_uint(cameraServices + m_iFOV)
    return fov

def setFOV(fov: int, retry: bool = False):
    while 1:
        pm.write_uint(cameraServices + m_iFOV, fov)
        time.sleep(0.05)