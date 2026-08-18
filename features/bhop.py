import time

import win32api

from functions import logutil, memfuncs, player_resolver
from functions.process_watcher import ProcessConnector


def Bhop_Update(processHandle, clientBaseAddress, Offsets):
    try:
        local_state = player_resolver.resolve_local_player(
            processHandle, clientBaseAddress, Offsets.offset
        )
        if local_state is None:
            return
        local_pawn = local_state.pawn

        if local_pawn:
            flags = memfuncs.ProcMemHandler.ReadInt(processHandle, local_pawn + Offsets.offset.m_fFlags)
            if win32api.GetAsyncKeyState(0x20) and flags & (1 << 0):
                memfuncs.ProcMemHandler.WriteInt(processHandle, clientBaseAddress + Offsets.offset.ButtonJump, 65537)
                time.sleep(0.01)
                memfuncs.ProcMemHandler.WriteInt(processHandle, clientBaseAddress + Offsets.offset.ButtonJump, 256)
    except Exception as e:
        logutil.debug(f"Bhop error: {e}")


def BhopThreadFunction(Options, Offsets):
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])
    while True:
        try:
            if not Options.get("EnableBhop", False):
                time.sleep(0.01)
                continue

            h = connector.ensure_process()
            client = connector.ensure_module("client.dll")
            Bhop_Update(h, client, Offsets)
            # tiny sleep to keep CPU sane
            time.sleep(0.001)
        except Exception as exc:
            logutil.debug(f"Bhop thread exception: {exc}")
            connector.invalidate()
            time.sleep(0.01)
