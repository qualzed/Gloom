from offsets import *
from src import entity
import pymem

def rgba(r, g, b, a=255):
    return r | (g << 8) | (b << 16) | (a << 24)

COLOR = rgba(255, 0, 0)

def glow():
    while 1:
        for pawn in entity.init_entity_list():
            glow = pawn + m_Glow
            pm.write_int(glow + m_glowColorOverride, COLOR)
            pm.write_int(glow + m_iGlowType, 3)
            pm.write_uchar(glow + m_bGlowing, 1)