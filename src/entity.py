from offsets import *

# Thanks 
# https://www.unknowncheats.me/forum/counter-strike-2-a/731242-cs2-understanding-offset-chains-entitylist-money-names-viewmatrix-etc.html
#

STRIDE = 0x70

def init_entity_list():
    entities = []

    local_pawn = pm.read_longlong(client + offsets['client.dll']['dwLocalPlayerPawn'])
    if not local_pawn:
        return

    local_team = pm.read_int(local_pawn + m_iTeamNum)

    entity_list = pm.read_longlong(client + dwEntityList)
    if not entity_list:
        return

    for i in range(1, 65):
        list_entry = pm.read_longlong(entity_list + 0x8 * ((i & 0x7FFF) >> 9) + 0x10)
        if not list_entry:
            continue

        controller = pm.read_longlong(list_entry + STRIDE * (i & 0x1FF))
        if not controller:
            continue

        pawn_handle = pm.read_int(controller + m_hPlayerPawn)
        if pawn_handle in (0, -1):
            continue

        list_entry = pm.read_longlong(entity_list + 0x8 * ((pawn_handle & 0x7FFF) >> 9) + 0x10)
        if not list_entry:
            continue

        pawn = pm.read_longlong(list_entry + STRIDE * (pawn_handle & 0x1FF))
        if not pawn or pawn == local_pawn:
            continue

        if pm.read_uchar(pawn + m_lifeState) != 0:
            continue
        if pm.read_int(pawn + m_iTeamNum) == local_team:
            continue

        entities.append(pawn)

    return entities