import time

from functions import logutil, memfuncs, player_resolver
from functions.process_watcher import ProcessConnector


def FovChangerThreadFunction(Options, Offsets):
    connector = ProcessConnector("cs2.exe", modules=["client.dll"])

    last_fov_written = None

    def _clamp(v, lo, hi):
        try:
            return max(lo, min(hi, int(v)))
        except Exception:
            return lo

    while True:
        try:
            process = connector.ensure_process()
            client = connector.ensure_module("client.dll")

            if not Options.get("EnableFovChanger", False):
                last_fov_written = None
                time.sleep(0.01)
                continue

            local_state = player_resolver.resolve_local_player(
                process, client, Offsets.offset
            )
            if local_state is None:
                time.sleep(0.005)
                continue

            local_pawn = local_state.pawn
            camera_services = memfuncs.ProcMemHandler.ReadPointer(
                process, local_pawn + Offsets.offset.m_pCameraServices
            )
            if not camera_services:
                time.sleep(0.005)
                continue

            desired_fov = _clamp(Options.get("FovChangeSize", 90), 60, 140)
            if desired_fov != last_fov_written:
                try:
                    memfuncs.ProcMemHandler.WriteInt(process, camera_services + Offsets.offset.m_iFOV, desired_fov)
                    last_fov_written = desired_fov
                except Exception:
                    pass

            time.sleep(0.003)

        except Exception as exc:
            logutil.debug(f"[fovchanger] loop exception: {exc}")
            connector.invalidate()
            time.sleep(0.01)





















