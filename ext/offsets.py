import json
from dataclasses import dataclass
from pathlib import Path

import requests

PROJECT_DIR = Path(__file__).resolve().parents[1]
OFFSET_FILES = ("offsets.json", "client_dll.json", "buttons.json")


@dataclass
class Offset:
    dwViewMatrix: int
    dwLocalPlayerPawn: int
    dwEntityList: int
    dwLocalPlayerController: int
    dwViewAngles: int
    dwGameRules: int
    dwSensitivity_sensitivity: int
    dwSensitivity: int
    dwPlantedC4: int
    dwGlobalVars: int
    ButtonJump: int
    m_hViewEntity: int
    m_hObserverPawn: int
    m_hPlayerPawn: int
    m_iHealth: int
    m_lifeState: int
    m_iTeamNum: int
    m_vOldOrigin: int
    m_pGameSceneNode: int
    m_modelState: int
    m_boneArray: int
    m_nodeToWorld: int
    m_sSanitizedPlayerName: int
    m_iIDEntIndex: int
    m_flFlashMaxAlpha: int
    m_fFlags: int
    m_iFOV: int
    m_pCameraServices: int
    m_bIsScoped: int
    m_vecViewOffset: int
    m_entitySpottedState: int
    m_bSpotted: int
    m_bBombPlanted: int
    m_iShotsFired: int
    m_pAimPunchServices: int
    m_aimPunchAngle: int
    m_bSpottedByMask: int
    m_vecVelocity: int
    m_pObserverServices: int
    m_iObserverMode: int
    m_hObserverTarget: int
    m_bMatchWaitingForResume: int
    m_bGameRestart: int


class Client:
    def __init__(self, manual_dump=False):
        self.cache_dir = PROJECT_DIR / ".cache"
        if manual_dump:
            self._load_from_file()
        else:
            self._load_from_url()

    def _load_from_url(self):
        try:
            self.offsets = self._get_json_from_url(
                "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json"
            )
            self.clientdll = self._get_json_from_url(
                "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json"
            )
            self.buttons = self._get_json_from_url(
                "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.json"
            )
            self._write_cache()
        except (OSError, ValueError, requests.RequestException) as error:
            print(f"Unable to get offsets online ({error}). Falling back to local cache...")
            self._load_from_file(self.cache_dir)

    @staticmethod
    def _get_json_from_url(url):
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

    def _write_cache(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        for filename, data in (
            ("offsets.json", self.offsets),
            ("client_dll.json", self.clientdll),
            ("buttons.json", self.buttons),
        ):
            with (self.cache_dir / filename).open("w", encoding="utf-8") as file:
                json.dump(data, file)

    def _load_from_file(self, base_path=None):
        preferred_path = Path(base_path) if base_path else PROJECT_DIR / "output"
        source_path = preferred_path
        if not all((source_path / filename).is_file() for filename in OFFSET_FILES):
            source_path = self.cache_dir

        try:
            self.offsets = self._load_json_from_file(source_path, "offsets.json")
            self.clientdll = self._load_json_from_file(source_path, "client_dll.json")
            self.buttons = self._load_json_from_file(source_path, "buttons.json")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Unable to load offset data from {source_path}: {error}"
            ) from error

    @staticmethod
    def _load_json_from_file(base_path, filename):
        with (Path(base_path) / filename).open("r", encoding="utf-8") as file:
            return json.load(file)

    def offset(self, name, default=0):
        try:
            return self.offsets["client.dll"][name]
        except KeyError:
            print(f"Offset {name} not found, defaulting to {default}.")
            return default

    def get(self, class_name, field_name, default=None):
        try:
            return self.clientdll["client.dll"]["classes"][class_name]["fields"][field_name]
        except KeyError:
            if default is not None:
                return default
            print(f"Warning: Netvar {class_name} -> {field_name} not found.")
            return 0

    def button(self, name):
        return self._get_value_from_dict(
            self.buttons, ["client.dll", name], f"Button {name} not found."
        )

    @staticmethod
    def _get_value_from_dict(data, keys, error_message):
        try:
            for key in keys:
                data = data[key]
            return data
        except KeyError as error:
            raise KeyError(error_message) from error


def get_offsets() -> Offset:
    client = Client()
    return Offset(
        dwViewMatrix=client.offset("dwViewMatrix"),
        dwLocalPlayerPawn=client.offset("dwLocalPlayerPawn"),
        dwEntityList=client.offset("dwEntityList"),
        dwLocalPlayerController=client.offset("dwLocalPlayerController"),
        dwViewAngles=client.offset("dwViewAngles"),
        dwGameRules=client.offset("dwGameRules"),
        dwSensitivity_sensitivity=client.offset("dwSensitivity_sensitivity"),
        dwSensitivity=client.offset("dwSensitivity"),
        dwPlantedC4=client.offset("dwPlantedC4", 0),
        dwGlobalVars=client.offset("dwGlobalVars", 0),
        ButtonJump=client.button("jump"),
        m_hObserverPawn=client.get("CCSPlayerController", "m_hObserverPawn"),
        m_hViewEntity=client.get("CPlayer_CameraServices", "m_hViewEntity"),
        m_hPlayerPawn=client.get("CCSPlayerController", "m_hPlayerPawn"),
        m_iHealth=client.get("C_BaseEntity", "m_iHealth"),
        m_lifeState=client.get("C_BaseEntity", "m_lifeState"),
        m_iTeamNum=client.get("C_BaseEntity", "m_iTeamNum"),
        m_vOldOrigin=client.get("C_BasePlayerPawn", "m_vOldOrigin"),
        m_pGameSceneNode=client.get("C_BaseEntity", "m_pGameSceneNode"),
        m_modelState=client.get("CSkeletonInstance", "m_modelState"),
        m_boneArray=128,
        m_nodeToWorld=client.get("CGameSceneNode", "m_nodeToWorld"),
        m_sSanitizedPlayerName=client.get(
            "CCSPlayerController", "m_sSanitizedPlayerName"
        ),
        m_iIDEntIndex=client.get("C_CSPlayerPawn", "m_iIDEntIndex"),
        m_flFlashMaxAlpha=client.get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
        m_fFlags=client.get("C_BaseEntity", "m_fFlags"),
        m_iFOV=client.get("CCSPlayerBase_CameraServices", "m_iFOV"),
        m_pCameraServices=client.get("C_BasePlayerPawn", "m_pCameraServices"),
        m_bIsScoped=client.get("C_CSPlayerPawn", "m_bIsScoped"),
        m_vecViewOffset=client.get("C_BaseModelEntity", "m_vecViewOffset"),
        m_entitySpottedState=client.get("C_CSPlayerPawn", "m_entitySpottedState"),
        m_bSpotted=client.get("EntitySpottedState_t", "m_bSpotted"),
        m_bBombPlanted=client.get("C_CSGameRules", "m_bBombPlanted"),
        m_iShotsFired=client.get("C_CSPlayerPawn", "m_iShotsFired"),
        m_pAimPunchServices=client.get(
            "C_CSPlayerPawn", "m_pAimPunchServices", 0x14B8
        ),
        m_aimPunchAngle=0x174,
        m_bSpottedByMask=client.get("EntitySpottedState_t", "m_bSpottedByMask"),
        m_vecVelocity=client.get("C_BaseEntity", "m_vecVelocity"),
        m_pObserverServices=client.get("C_BasePlayerPawn", "m_pObserverServices"),
        m_iObserverMode=client.get("CPlayer_ObserverServices", "m_iObserverMode"),
        m_hObserverTarget=client.get("CPlayer_ObserverServices", "m_hObserverTarget"),
        m_bMatchWaitingForResume=client.get(
            "C_CSGameRules", "m_bMatchWaitingForResume"
        ),
        m_bGameRestart=client.get("C_CSGameRules", "m_bGameRestart"),
    )
