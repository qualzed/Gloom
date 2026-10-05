import time
from offsets import *
from src.scanner import scan

PROJECTILE = "smokegrenade_projectile"

def resolve_flag():
    try:
        return client_dll['client.dll']['classes']['C_SmokeGrenadeProjectile']['fields']['m_bDidSmokeEffect']
    except KeyError:
        raise SystemExit("C_SmokeGrenadeProjectile.m_bDidSmokeEffect not found in the dump")


def nosmoke():
    flag = resolve_flag()

    while True:
        time.sleep(0.05)

        try:
            for projectile in scan((PROJECTILE,))[PROJECTILE]:
                pm.write_uchar(projectile + flag, 1)
        except Exception:
            continue