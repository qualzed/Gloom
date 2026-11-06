from pypresence import Presence
import os, time

client_id = "1559828113758887968" # Мне впадлу прятать, делайте с ним что хотите
RPC = Presence(client_id)
try:
    RPC.connect()
except:
    pass

start_time = time.time()

def StartRPC():
    try:
        RPC.update(
            large_image="icon",
            start=start_time,
            details="Counter-Strike 2 External Software",
            buttons=[{"label":"DM's", "url":"https://guns.lol/qualzed"}]
        )
    except Exception as e:
        RPC.connect()
