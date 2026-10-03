import pymem
import pymem.process
import requests

BASE_URL = 'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/'

pm = pymem.Pymem("cs2.exe")
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

offsets = requests.get(BASE_URL + 'offsets.json').json()
client_dll = requests.get(BASE_URL + 'client_dll.json').json()
client_dll_cs = requests.get(BASE_URL + 'client_dll.cs').text

_client_offsets = offsets['client.dll']
_classes = client_dll['client.dll']['classes']


def field(cls, name):
    return _classes[cls]['fields'][name]


def cs_offset(name):
    return int(client_dll_cs.split(f"{name} = 0x")[1].split(";")[0].strip(), 16)


dwEntityList = 40982552
dwGameEntitySystem = _client_offsets['dwGameEntitySystem']
dwLocalPlayerPawn = _client_offsets['dwLocalPlayerPawn']
dwLocalPlayerController = _client_offsets['dwLocalPlayerController']
dwViewMatrix = _client_offsets['dwViewMatrix']
dwPlantedC4 = _client_offsets['dwPlantedC4']

m_iTeamNum = field('C_BaseEntity', 'm_iTeamNum')
m_lifeState = field('C_BaseEntity', 'm_lifeState')
m_iHealth = field('C_BaseEntity', 'm_iHealth')
m_pGameSceneNode = field('C_BaseEntity', 'm_pGameSceneNode')
m_modelState = field('CSkeletonInstance', 'm_modelState')
m_vecAbsOrigin = field('CGameSceneNode', 'm_vecAbsOrigin')

m_hPlayerPawn = field('CCSPlayerController', 'm_hPlayerPawn')
m_iszPlayerName = field('CBasePlayerController', 'm_iszPlayerName')
m_iDesiredFOV = field('CBasePlayerController', 'm_iDesiredFOV')

m_ArmorValue = field('C_CSPlayerPawn', 'm_ArmorValue')
m_flFlashMaxAlpha = field('C_CSPlayerPawnBase', 'm_flFlashMaxAlpha')
m_pCameraServices = field('C_BasePlayerPawn', 'm_pCameraServices')
m_iFOV = field('CCSPlayerBase_CameraServices', 'm_iFOV')

m_AttributeManager = field('C_EconEntity', 'm_AttributeManager')
m_Item = field('C_AttributeContainer', 'm_Item')
m_iItemDefinitionIndex = field('C_EconItemView', 'm_iItemDefinitionIndex')

m_flTimerLength = field('C_PlantedC4', 'm_flTimerLength')
m_flDefuseLength = field('C_PlantedC4', 'm_flDefuseLength')
m_bBeingDefused = field('C_PlantedC4', 'm_bBeingDefused')

m_Glow = field('C_BaseModelEntity', 'm_Glow')
m_iGlowType = field('CGlowProperty', 'm_iGlowType')
m_glowColorOverride = field('CGlowProperty', 'm_glowColorOverride')
m_bGlowing = field('CGlowProperty', 'm_bGlowing')

m_bFlashing = cs_offset('m_bFlashing')