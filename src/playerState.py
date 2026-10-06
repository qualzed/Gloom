from offsets import *

def IsInGame():
     local_player = pm.read_longlong(client + dwLocalPlayerPawn)
     if local_player:
          if 0 < pm.read_int(local_player + m_iHealth) <= 100:
               return True
          else:
               return False
     else:
          return False