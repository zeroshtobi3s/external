from functions import memfuncs
from functions import logutil
from functions.process_watcher import ProcessConnector
import time

def BombTimerThread(SharedBombState, SharedOffsets):
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])
    TOTAL_TIME = 40.0
    SharedBombState.bombTimeTotal = TOTAL_TIME
    SharedBombState.bombPlanted = False
    SharedBombState.bombTimeLeft = -1.0
    SharedBombState.site = ""
    SharedBombState.isDefusing = False
    SharedBombState.defuseTimeLeft = -1.0

    c4_ticking_offset = 4512
    c4_site_offset = 4516
    c4_blow_offset = 4560
    c4_timer_len_offset = 4568
    c4_being_defused_offset = 4572
    c4_defuse_countdown_offset = 4592
    c4_defused_offset = 4596

    while True:
        try:
            processHandle = connector.ensure_process()
            clientBaseAddress = connector.ensure_module("client.dll")
            off = SharedOffsets.offset

            # 1. GameRules check
            gameRule = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + getattr(off, "dwGameRules", 0))
            bomb_planted_gamerules = False
            if gameRule:
                bomb_planted_gamerules = memfuncs.ProcMemHandler.ReadBool(processHandle, gameRule + getattr(off, "m_bBombPlanted", 0x9FD))

            # 2. PlantedC4 pointer resolution
            planted_c4_ptr = 0
            if getattr(off, "dwPlantedC4", 0):
                base_ptr = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + off.dwPlantedC4)
                if base_ptr:
                    # Test if base_ptr itself is C_PlantedC4 or pointer to pointer
                    ticking_direct = memfuncs.ProcMemHandler.ReadBool(processHandle, base_ptr + c4_ticking_offset)
                    if ticking_direct:
                        planted_c4_ptr = base_ptr
                    else:
                        deref = memfuncs.ProcMemHandler.ReadPointer(processHandle, base_ptr)
                        if deref:
                            planted_c4_ptr = deref

            if not bomb_planted_gamerules and not planted_c4_ptr:
                SharedBombState.bombPlanted = False
                SharedBombState.bombTimeLeft = -1.0
                SharedBombState.isDefusing = False
                SharedBombState.defuseTimeLeft = -1.0
                time.sleep(0.05)
                continue

            if planted_c4_ptr:
                defused = memfuncs.ProcMemHandler.ReadBool(processHandle, planted_c4_ptr + c4_defused_offset)
                if defused:
                    SharedBombState.bombPlanted = False
                    SharedBombState.bombTimeLeft = -1.0
                    SharedBombState.isDefusing = False
                    SharedBombState.defuseTimeLeft = -1.0
                    time.sleep(0.05)
                    continue

                c4_blow = memfuncs.ProcMemHandler.ReadFloat(processHandle, planted_c4_ptr + c4_blow_offset)
                timer_len = memfuncs.ProcMemHandler.ReadFloat(processHandle, planted_c4_ptr + c4_timer_len_offset)
                site_num = memfuncs.ProcMemHandler.ReadInt(processHandle, planted_c4_ptr + c4_site_offset)
                being_defused = memfuncs.ProcMemHandler.ReadBool(processHandle, planted_c4_ptr + c4_being_defused_offset)
                defuse_countdown = memfuncs.ProcMemHandler.ReadFloat(processHandle, planted_c4_ptr + c4_defuse_countdown_offset)

                SharedBombState.bombPlanted = True
                SharedBombState.site = "B" if site_num == 1 else "A"
                if timer_len > 0:
                    SharedBombState.bombTimeTotal = float(timer_len)

                dwGlobalVars_offset = getattr(off, "dwGlobalVars", 34164024)
                dwGlobalVars = memfuncs.ProcMemHandler.ReadPointer(processHandle, clientBaseAddress + dwGlobalVars_offset) if dwGlobalVars_offset else 0
                curtime = 0.0
                if dwGlobalVars:
                    for g_off in [0x30, 0x2C, 0x34, 0x00]:
                        val = memfuncs.ProcMemHandler.ReadFloat(processHandle, dwGlobalVars + g_off)
                        if val > 0 and (c4_blow <= 0 or abs(c4_blow - val) < 60.0):
                            curtime = val
                            break

                if c4_blow > 0:
                    if curtime > 0 and c4_blow >= curtime:
                        left = max(0.0, c4_blow - curtime)
                    else:
                        left = max(0.0, c4_blow)
                    SharedBombState.bombTimeLeft = round(left, 1)
                else:
                    SharedBombState.bombTimeLeft = -1.0

                SharedBombState.isDefusing = being_defused
                if being_defused and defuse_countdown > 0 and curtime > 0:
                    SharedBombState.defuseTimeLeft = max(0.0, round(defuse_countdown - curtime, 1))
                else:
                    SharedBombState.defuseTimeLeft = -1.0
            else:
                SharedBombState.bombPlanted = bomb_planted_gamerules
                SharedBombState.bombTimeLeft = -1.0

            time.sleep(0.03)

        except Exception as exc:
            logutil.debug(f"[bombtimer] loop exception: {exc}")
            SharedBombState.bombPlanted = False
            SharedBombState.bombTimeLeft = -1.0
            connector.invalidate()
            time.sleep(0.1)
