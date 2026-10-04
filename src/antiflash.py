from offsets import *
import pymem, time

def antiflash():
     while 1:
          time.sleep(0.05)
          local_player = pm.read_longlong(client + dwLocalPlayerPawn)
          pm.write_float(local_player + m_flFlashMaxAlpha, 0.0)