import time

import win32api
import win32gui

from functions import gameinput, logutil, memfuncs, player_resolver
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

            local_state = player_resolver.resolve_local_player(
                process, client, Offsets.offset
            )
            if local_state is None:
                time.sleep(0.002)
                continue
            local_pawn = local_state.pawn

            local_id = memfuncs.ProcMemHandler.ReadInt(process, local_pawn + Offsets.offset.m_iIDEntIndex)
            if local_id <= 0:
                time.sleep(0.002)
                continue

            target = player_resolver.resolve_entity_handle(
                process, local_state.entity_list, local_id
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

