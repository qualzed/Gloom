import ctypes
import mmap

MAGIC = 0x4D575231


class Config(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint32),
        ("esp_hp", ctypes.c_bool),
        ("esp_name", ctypes.c_bool),
        ("esp_weapon", ctypes.c_bool),
        ("esp_skeleton", ctypes.c_bool),
        ("esp_box", ctypes.c_bool),
        ("aim_enabled", ctypes.c_bool),
        ("antismoke", ctypes.c_bool),
        ("antiflash", ctypes.c_bool),
        ("fov_enabled", ctypes.c_bool),
        ("glow_enabled", ctypes.c_bool),
        ("aim_fov", ctypes.c_float),
        ("fov_value", ctypes.c_float),
        ("glow_r", ctypes.c_float),
        ("glow_g", ctypes.c_float),
        ("glow_b", ctypes.c_float),
    ]


DEFAULTS = {
    "esp_hp": True,
    "esp_name": True,
    "esp_weapon": True,
    "esp_skeleton": True,
    "esp_box": True,
    "aim_enabled": False,
    "antismoke": False,
    "antiflash": False,
    "fov_enabled": False,
    "glow_enabled": False,
    "aim_fov": 20.0,
    "fov_value": 90.0,
    "glow_r": 1.0,
    "glow_g": 0.25,
    "glow_b": 0.25,
}

try:
    _map = mmap.mmap(-1, ctypes.sizeof(Config), tagname="moonware_config")
except TypeError:
    _map = mmap.mmap(-1, ctypes.sizeof(Config))

cfg = Config.from_buffer(_map)

if cfg.magic != MAGIC:
    for name, value in DEFAULTS.items():
        setattr(cfg, name, value)
    cfg.magic = MAGIC