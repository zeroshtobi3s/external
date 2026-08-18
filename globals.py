import ctypes
from pathlib import Path

import win32api
import win32gui

from ext import offsets
from ext.datatypes import *

# Enable Per-Monitor DPI Awareness so Windows does not virtualize / scale screen metrics
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def get_screen_resolution():
    """Retrieve actual physical game client resolution."""
    try:
        hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
        if hwnd and win32gui.IsWindow(hwnd):
            rect = win32gui.GetClientRect(hwnd)
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            if w > 100 and h > 100:
                return int(w), int(h)
    except Exception:
        pass
    w = win32api.GetSystemMetrics(0)
    h = win32api.GetSystemMetrics(1)
    return int(w), int(h)

SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_resolution()

def update_screen_size():
    global SCREEN_WIDTH, SCREEN_HEIGHT
    w, h = get_screen_resolution()
    SCREEN_WIDTH = w
    SCREEN_HEIGHT = h
    return w, h

GAME_OFFSETS = offsets.get_offsets()

PROJECT_DIR = Path(__file__).resolve().parent
SAVE_FILE = str(PROJECT_DIR / "settings.json")

CHEAT_SETTINGS = {
    "EnableAntiFlashbang": False,
    "EnableFovChanger": False,
    "FovChangeSize": 90,
	
    "EnableAimbot": True,
    "EnableAimbotPrediction": True,
    "EnableAimbotTeamCheck": False,
    "EnableAimbotVisibilityCheck": False,
    "AimbotFOV": 75,
    "AimbotSmoothing": 2,
    "AimPosition": "Head",
    "AimbotKey": 6,
	
    "EnableRecoilControl": False,
    "RecoilControlSmoothing": 1.0,

    "EnableTriggerbot": True,
    "EnableTriggerbotKeyCheck": True,
    "TriggerbotKey": 17,
    "EnableTriggerbotTeamCheck": False,

    "EnableESPDistanceRendering": True,
    "EnableESPTeamCheck": False,
    "EnableESPSkeletonRendering": True,
    "EnableESPBoxRendering": True,
    "EnableESPTracerRendering": False,
    "EnableESPNameText": True,
    "EnableESPHealthBarRendering": True,
    "EnableESPHealthText": False,
    "EnableESPDistanceText": True,

    "EnableESPBombTimer": True,
    
    "CT_color": "#4DA2FF",
    "T_color": "#FF6A5A",
    "FOV_color": "#FFFFFF",

    "EnableBhop": False,

    "EnableDiscordRPC": True,

    "EnableShowSpectators": True,

    "EnableOverlayRaylibFont": True,

    "ESP_HealthSyncSkeleton": True,
    "ESP_HealthSyncBar": True,
    "ESP_SkeletonThicknessScale": 1.0,
    "ESP_BoxThicknessScale": 1.0,
    "ESP_HealthBarThicknessScale": 1.0,

    "ESP_VisibleCheckBox": False,

}


RCS_CTRL_BY_AIMBOT = False
