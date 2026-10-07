import json, os

CONFIG_FILE = "config.json"

_esp: bool = False
_fov: bool = False
_antiflash: bool = False
_glow: bool = False
_trigger: bool = False
_aim: bool = False
_antismoke: bool = False

def UpdateJSON(row: str, data):
     global _esp, _aim, _glow, _antiflash, _antismoke, _fov, _trigger
     config = {}

     if os.path.exists(CONFIG_FILE):
          with open(CONFIG_FILE, "r", encoding="utf-8") as file:
               try:
                    config = json.load(file)
               except json.JSONDecodeError:
                    config = {}

     config[row] = data
     globals()[f"_{row}"] = data
     
     with open(CONFIG_FILE, "w", encoding="utf-8") as file:
          json.dump(config, file, indent=5, ensure_ascii=False)

def ReadJSON():
     global _esp, _aim, _glow, _antiflash, _antismoke, _fov, _trigger
     config = None
     try:
          with open(CONFIG_FILE, "r", encoding="utf-8") as f:
               config = json.load(f)
          
          _esp = config['esp']
          _aim = config['aim']
          _glow = config['glow']
          _antiflash = config['antiflash']
          _antismoke = config['antismoke']
          _fov = config['fov']
          _trigger = config['trigger']
     except:
          print("JSON was not found!")