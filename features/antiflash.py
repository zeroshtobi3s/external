import time

from functions import logutil, memfuncs, player_resolver
from functions.process_watcher import ProcessConnector


def AntiFlashThreadFunction(Options, Offsets):
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])

    last_value = None

    while True:
        try:
            process = connector.ensure_process()
            client = connector.ensure_module("client.dll")

            local_state = player_resolver.resolve_local_player(
                process, client, Offsets.offset
            )
            if local_state is None:
                time.sleep(0.005)
                continue

            local_pawn = local_state.pawn
            desired = 0.0 if Options.get("EnableAntiFlashbang", False) else 255.0
            if desired != last_value:
                try:
                    memfuncs.ProcMemHandler.WriteFloat(
                        process,
                        local_pawn + Offsets.offset.m_flFlashMaxAlpha,
                        desired,
                    )
                    last_value = desired
                except Exception:
                    pass

            time.sleep(0.002)

        except Exception as exc:
            logutil.debug(f"[antiflash] loop exception: {exc}")
            connector.invalidate()
            time.sleep(0.01)

