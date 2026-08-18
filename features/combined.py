import win32api
import win32gui

from functions import gameinput, logutil, memfuncs, player_resolver


def Triggerbot_AntiFlash_Update(processHandle, clientBaseAddress, Offsets, Options):
    try:
        local_state = player_resolver.resolve_local_player(
            processHandle, clientBaseAddress, Offsets.offset
        )
        if local_state is None:
            return
        local_player = local_state.pawn

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
        if not (
            game_is_foreground
            and triggerbot_is_active
            and (key_is_active or key_check_is_disabled)
        ):
            return

        target_handle = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_player + Offsets.offset.m_iIDEntIndex
        )
        target_entity = player_resolver.resolve_entity_handle(
            processHandle, local_state.entity_list, target_handle
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
    except Exception as error:  # noqa: BLE001 - native memory errors are platform-specific.
        logutil.debug(f"[combined] update failed: {error}")
