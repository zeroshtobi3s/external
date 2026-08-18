import multiprocessing
import os
import threading
import time

import keyboard
import serial
import serial.tools.list_ports
import win32api
import win32con
import win32process

import globals
from features import (
    aimbot,
    antiflash,
    bhop,
    bombtimer,
    discodrpc,
    esp,
    fovchanger,
    rcs,
    spectator,
    triggerbot,
)
from functions import config_store, logutil
from functions.process_watcher import ProcessConnector
from GUI import gui_mainloop, gui_util


def register_hotkeys():
    keyboard.add_hotkey("end", callback=lambda: os._exit(0))
    keyboard.add_hotkey("insert", callback=gui_util.hide_dpg)
    keyboard.add_hotkey("home", callback=gui_util.streamproof_toggle)


def SaveConfig(options):
    return config_store.save_settings(options, globals.SAVE_FILE)


def LoadConfig():
    loaded_settings = config_store.load_settings(globals.CHEAT_SETTINGS, globals.SAVE_FILE)
    globals.CHEAT_SETTINGS.clear()
    globals.CHEAT_SETTINGS.update(loaded_settings)

def ConfigSaverThread(shared_dict):
    last_saved = None
    while True:
        try:
            current = dict(shared_dict)
            if current != last_saved and SaveConfig(current):
                last_saved = current
        except Exception:
            pass
        time.sleep(1.0)


if __name__ == "__main__":
    register_hotkeys()

    print(" _   _ ______ _____   ____  _   _ \n| \\ | |  ____|  __ \\ / __ \\| \\ | |\n|  \\| | |__  | |__) | |  | |  \\| |\n| . ` |  __| |  _  /| |  | | . ` |\n| |\\  | |____| | \\ \\| |__| | |\\  |\n|_| \\_|______|_|  \\_\\\\____/|_| \\_|\n\n             - NERON v1.0\n             - developed by khorami.dev\n             - https://github.com/SadraKhorami/cs2_neron_external")

    win32process.SetPriorityClass(
        win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, win32api.GetCurrentProcessId()),
        win32process.HIGH_PRIORITY_CLASS
    )
    multiprocessing.freeze_support()

    COM_PORT = None
    use_arduino = "N"
    if use_arduino.upper() == "Y":
        for index, port in enumerate([p.device for p in serial.tools.list_ports.comports()]):
            print(f"[{index}] {port}")
        COM_PORT = input("Select COM Port: ")
        ARDUINO_HANDLE = serial.Serial([p.device for p in serial.tools.list_ports.comports()][int(COM_PORT)], 9600)
    else:
        ARDUINO_HANDLE = None

    # Process & module
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])
    ProcessObject = connector.ensure_process()
    ClientModuleAddress = connector.ensure_module("client.dll")

    # Config
    LoadConfig()
    SharedOptions = globals.CHEAT_SETTINGS

    saver_thread = threading.Thread(target=ConfigSaverThread, args=(SharedOptions,), daemon=True)
    saver_thread.start()

    # Offsets & Runtime State
    class SimpleState:
        pass

    SharedOffsets = SimpleState()
    SharedOffsets.offset = globals.GAME_OFFSETS

    SharedRuntime = SimpleState()
    SharedRuntime.spectators = []

    GUI_thread = threading.Thread(target=gui_mainloop.run_gui, args=(SharedOptions, SharedRuntime,), daemon=True)
    GUI_thread.start()

    # Overlay
    try:
        esp.pme.overlay_init(target="Counter-Strike 2")
    except Exception:
        esp.pme.overlay_init(title="ESP-Overlay")
    fps = esp.pme.get_monitor_refresh_rate()
    try:
        target_fps = min(max(int(fps) + 20, 90), 240)
    except Exception:
        target_fps = fps
    esp.pme.set_fps(target_fps)

    # FOV changer
    FOV_thread = threading.Thread(target=fovchanger.FovChangerThreadFunction, args=(SharedOptions, SharedOffsets,), daemon=True)
    FOV_thread.start()

    # Anti-Flash
    AntiFlash_thread = threading.Thread(target=antiflash.AntiFlashThreadFunction, args=(SharedOptions, SharedOffsets,), daemon=True)
    AntiFlash_thread.start()

    # Triggerbot
    Trigger_thread = threading.Thread(target=triggerbot.TriggerbotThreadFunction, args=(SharedOptions, SharedOffsets,), daemon=True)
    Trigger_thread.start()

    # Bhop
    Bhop_thread = threading.Thread(target=bhop.BhopThreadFunction, args=(SharedOptions, SharedOffsets,), daemon=True)
    Bhop_thread.start()

    # Bomb timer
    SharedBombState = SimpleState()
    SharedBombState.bombPlanted = False
    SharedBombState.bombTimeLeft = -1
    Bomb_thread = threading.Thread(target=bombtimer.BombTimerThread, args=(SharedBombState, SharedOffsets,), daemon=True)
    Bomb_thread.start()

    # Discord RPC
    discord_rpc_thread = threading.Thread(target=discodrpc.DiscordRpcThread, args=(SharedOptions,), daemon=True)
    discord_rpc_thread.start()

    # Spectator monitor
    Spectator_thread = threading.Thread(
        target=spectator.SpectatorThreadFunction,
        args=(SharedOptions, SharedOffsets, SharedRuntime,),
        daemon=True
    )
    Spectator_thread.start()
    logutil.debug("[main] spectator monitor: started")

    overlay_logged_once = False
    while esp.pme.overlay_loop():
        try:
            ProcessObject = connector.ensure_process()
            ClientModuleAddress = connector.ensure_module("client.dll")
        except Exception:
            connector.invalidate()
            time.sleep(0.5)
            continue

        if not overlay_logged_once:
            logutil.debug("[main] overlay loop entered; Spec List will be drawn from features/esp.py.")
            logutil.debug("[main] rendering Spec List on the game frame (inside ESP begin/end drawing)")
            overlay_logged_once = True

        try:
            esp.ESP_Update(ProcessObject, ClientModuleAddress, SharedOptions, SharedOffsets, SharedBombState, SharedRuntime)

            try:
                _ = len(SharedRuntime.spectators)
            except Exception:
                pass

            if SharedOptions.get("EnableAimbot", False) and win32api.GetAsyncKeyState(SharedOptions.get("AimbotKey", 6)) & 0x8000:
                aimbot.Aimbot_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)

            rcs.RecoilControl_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)
        except Exception:
            connector.invalidate()
            time.sleep(0.01)
            continue
