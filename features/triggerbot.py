import time

import win32api
import win32gui

from functions import entity_list, gameinput, logutil, memfuncs
from functions.process_watcher import ProcessConnector


def TriggerbotThreadFunction(Options, Offsets):
    """Dedicated triggerbot worker. Keeps sleeps out of the overlay loop."""
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])

    while True:
        try:
            if not Options.get("EnableTriggerbot", False):
                time.sleep(0.01)
                continue

            process = connector.ensure_process()
            client = connector.ensure_module("client.dll")

            # Optional key gating
            key_ok = win32api.GetAsyncKeyState(Options.get("TriggerbotKey", 17)) or not Options.get("EnableTriggerbotKeyCheck", True)
            if not key_ok:
                time.sleep(0.002)
                continue

            # Limit to when game window is foreground
            if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != "Counter-Strike 2":
                time.sleep(0.005)
                continue

            local_pawn = memfuncs.ProcMemHandler.ReadPointer(process, client + Offsets.offset.dwLocalPlayerPawn)
            if not local_pawn:
                time.sleep(0.002)
                continue

            local_id = memfuncs.ProcMemHandler.ReadInt(process, local_pawn + Offsets.offset.m_iIDEntIndex)
            if local_id <= 0:
                time.sleep(0.002)
                continue

            entlist = memfuncs.ProcMemHandler.ReadPointer(process, client + Offsets.offset.dwEntityList)
            if not entlist:
                time.sleep(0.002)
                continue

            entry = memfuncs.ProcMemHandler.ReadPointer(
                process, entity_list.entity_list_chunk_address(entlist, local_id)
            )
            if not entry:
                time.sleep(0.002)
                continue

            target = memfuncs.ProcMemHandler.ReadPointer(
                process, entity_list.entity_slot_address(entry, local_id)
            )
            if not target:
                time.sleep(0.002)
                continue

            if Options.get("EnableTriggerbotTeamCheck", False):
                tgt_team = memfuncs.ProcMemHandler.ReadInt(process, target + Offsets.offset.m_iTeamNum)
                me_team = memfuncs.ProcMemHandler.ReadInt(process, local_pawn + Offsets.offset.m_iTeamNum)
                if tgt_team == me_team:
                    time.sleep(0.002)
                    continue

            hp = memfuncs.ProcMemHandler.ReadInt(process, target + Offsets.offset.m_iHealth)
            if hp > 0 and not win32api.GetAsyncKeyState(0x01):
                gameinput.LeftClick()

            time.sleep(0.0015)

        except Exception as exc:
            logutil.debug(f"[triggerbot] loop exception: {exc}")
            connector.invalidate()
            time.sleep(0.01)

