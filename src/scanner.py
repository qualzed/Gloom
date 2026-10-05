import struct
from offsets import *

CHUNKS = 64
SLOTS = 512
STRIDE = 0x70

names = {}

def class_name(pointer):
    if pointer not in names:
        try:
            names[pointer] = pm.read_string(pointer, 32)
        except Exception:
            return ""
    return names[pointer]

def scan(wanted):
    found = {name: [] for name in wanted}
    entity_list = pm.read_longlong(client + dwEntityList)

    for chunk_index in range(CHUNKS):
        chunk = pm.read_longlong(entity_list + 0x10 + 8 * chunk_index)
        if not chunk:
            continue

        try:
            data = pm.read_bytes(chunk, SLOTS * STRIDE)
        except Exception:
            continue

        for slot in range(SLOTS):
            entity, = struct.unpack_from("Q", data, slot * STRIDE)
            pointer, = struct.unpack_from("Q", data, slot * STRIDE + 0x20)
            if not entity or not pointer:
                continue

            name = class_name(pointer)
            if name in found:
                found[name].append(entity)

    return found