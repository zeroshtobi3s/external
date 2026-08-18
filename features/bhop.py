import time

import win32api

from functions import entity_list, logutil, memfuncs
from functions.process_watcher import ProcessConnector


def Bhop_Update(processHandle, clientBaseAddress, Offsets):
    try:
        localPlayer = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerController)
        if not localPlayer:
            return

        localPawn = memfuncs.ProcMemHandler.ReadInt(processHandle, localPlayer + Offsets.offset.m_hPlayerPawn)
        if not localPawn:
            return

        entityList = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + Offsets.offset.dwEntityList)
        listEntry = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, entity_list.entity_list_chunk_address(entityList, localPawn)
        )
        if not listEntry:
            return
        localPawn = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, entity_list.entity_slot_address(listEntry, localPawn)
        )

        if localPawn:
            flags = memfuncs.ProcMemHandler.ReadInt(processHandle, localPawn + Offsets.offset.m_fFlags)
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
