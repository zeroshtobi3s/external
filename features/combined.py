import win32api
import win32gui

from functions import entity_list, gameinput, logutil, memfuncs


def Triggerbot_AntiFlash_Update(processHandle, clientBaseAddress, Offsets, Options):
    local_player = memfuncs.ProcMemHandler.ReadPointer(
        processHandle, clientBaseAddress + Offsets.offset.dwLocalPlayerPawn
    )
    if not local_player:
        return

    try:
        flash_alpha = 0.0 if Options.get("EnableAntiFlashbang", False) else 255.0
        memfuncs.ProcMemHandler.WriteFloat(
            processHandle,
            local_player + Offsets.offset.m_flFlashMaxAlpha,
            flash_alpha,
        )

        game_is_foreground = (
            win32gui.GetWindowText(win32gui.GetForegroundWindow()) == "Counter-Strike 2"
        )
        key_is_active = win32api.GetAsyncKeyState(Options.get("TriggerbotKey", 17))
        triggerbot_is_active = Options.get("EnableTriggerbot", False)
        key_check_is_disabled = not Options.get("EnableTriggerbotKeyCheck", True)
        if not (game_is_foreground and triggerbot_is_active and (key_is_active or key_check_is_disabled)):
            return

        target_handle = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_player + Offsets.offset.m_iIDEntIndex
        )
        if target_handle <= 0:
            return

        entity_list_address = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwEntityList
        )
        if not entity_list_address:
            return
        entity_chunk = memfuncs.ProcMemHandler.ReadPointer(
            processHandle,
            entity_list.entity_list_chunk_address(entity_list_address, target_handle),
        )
        if not entity_chunk:
            return
        target_entity = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, entity_list.entity_slot_address(entity_chunk, target_handle)
        )
        if not target_entity:
            return

        target_team = memfuncs.ProcMemHandler.ReadInt(
            processHandle, target_entity + Offsets.offset.m_iTeamNum
        )
        local_team = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_player + Offsets.offset.m_iTeamNum
        )
        if Options.get("EnableTriggerbotTeamCheck", False) and target_team == local_team:
            return

        target_health = memfuncs.ProcMemHandler.ReadInt(
            processHandle, target_entity + Offsets.offset.m_iHealth
        )
        if target_health > 0 and not win32api.GetAsyncKeyState(0x01):
            gameinput.LeftClick()
    except Exception as error:  # noqa: BLE001 - memory API exceptions are platform-specific.
        logutil.debug(f"[combined] update failed: {error}")
