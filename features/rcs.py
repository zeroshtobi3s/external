import win32gui

import globals
from ext.datatypes import Vector2
from functions import gameinput, logutil, memfuncs, player_resolver

old_punch_x = 0.0
old_punch_y = 0.0


def RecoilControl_Update(processHandle, clientBaseAddress, Offsets, Options, ARDUINO_HANDLE):
    global old_punch_x, old_punch_y

    try:
        if win32gui.GetWindowText(win32gui.GetForegroundWindow()) != "Counter-Strike 2":
            return
        if not Options.get("EnableRecoilControl", False):
            return

        local_state = player_resolver.resolve_local_player(
            processHandle, clientBaseAddress, Offsets.offset
        )
        if local_state is None:
            return
        local_player = local_state.pawn

        shots_fired = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_player + Offsets.offset.m_iShotsFired
        )
        aim_punch_services = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, local_player + Offsets.offset.m_pAimPunchServices
        )
        if not aim_punch_services:
            return
        aim_punch_x = memfuncs.ProcMemHandler.ReadFloat(
            processHandle, aim_punch_services + Offsets.offset.m_aimPunchAngle
        )
        aim_punch_y = memfuncs.ProcMemHandler.ReadFloat(
            processHandle, aim_punch_services + Offsets.offset.m_aimPunchAngle + 0x4
        )

        sensitivity_base = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwSensitivity
        )
        if not sensitivity_base:
            return
        sensitivity = max(
            0.001,
            memfuncs.ProcMemHandler.ReadFloat(
                processHandle,
                sensitivity_base + Offsets.offset.dwSensitivity_sensitivity,
            ),
        )

        if 1 < shots_fired < 999999 and not globals.RCS_CTRL_BY_AIMBOT:
            delta_x = (aim_punch_x - old_punch_x) * -1.0
            delta_y = (aim_punch_y - old_punch_y) * -1.0
            move_x = (delta_y * 2.0 / sensitivity) / -0.022
            move_y = (delta_x * 2.0 / sensitivity) / 0.022

            current_mouse = gameinput.getCurrentMousePosition()
            target_mouse = Vector2(
                current_mouse.x + move_x,
                current_mouse.y + move_y,
            )
            smoothing = max(
                1.0,
                min(float(Options.get("RecoilControlSmoothing", 1.0)), 3.0),
            )
            next_mouse = Vector2(
                current_mouse.x + (target_mouse.x - current_mouse.x) / smoothing,
                current_mouse.y + (target_mouse.y - current_mouse.y) / smoothing,
            )

            if ARDUINO_HANDLE is not None:
                gameinput.moveMouseToLocationArdunio(next_mouse, handle=ARDUINO_HANDLE)
            else:
                gameinput.moveMouseToLocation(next_mouse)

            old_punch_x = aim_punch_x
            old_punch_y = aim_punch_y
        else:
            old_punch_x = 0.0
            old_punch_y = 0.0
    except Exception as error:  # noqa: BLE001 - native memory errors are environment-specific.
        logutil.debug(f"[rcs] update failed: {error}")
