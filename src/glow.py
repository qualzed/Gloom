from offsets import *
import pymem

def rgba(r, g, b, a=255):
    return r | (g << 8) | (b << 16) | (a << 24)

COLOR = rgba(255, 0, 0)

def glow_entity(entity_pawn_addr):
    glow = entity_pawn_addr + m_Glow
    pm.write_int(glow + m_glowColorOverride, COLOR)
    pm.write_int(glow + m_iGlowType, 3)
    pm.write_uchar(glow + m_bGlowing, 1)