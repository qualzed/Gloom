from offsets import *
from src import playerState
import pymem, time
from internal import crashlog

def antiflash():
     while 1:
          if not playerState.IsInGame():
               continue
          time.sleep(0.05)
          try:
               local_player = pm.read_longlong(client + dwLocalPlayerPawn)
               pm.write_float(local_player + m_flFlashMaxAlpha, 0.0)
          except Exception as e:
               crashlog.catchError(e, __name__, e.__traceback__.tb_lineno)
               pass