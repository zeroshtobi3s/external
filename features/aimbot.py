import time

import pymem

import globals
from ext.datatypes import Entity, Vector2, Vector3
from functions import (
    aim_settings,
    calculations,
    entity_list,
    gameinput,
    logutil,
    memfuncs,
    player_resolver,
)


def is_valid_address(address):
    return address is not None and 0x10000 < address < 0x7FFFFFFFFFFF


def GetPlayers(processHandle, clientBaseAddress, LocalPlayer, AimBoneID, Options, Offsets):
    entities = []
    try:
        entity_list_address = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwEntityList
        )
    except pymem.exception.MemoryReadError as error:
        logutil.debug(f"[aimbot] could not read entity list: {error}")
        return entities

    for index in range(1, 65):
        try:
            entity = Entity()
            chunk_address = entity_list.entity_list_chunk_address(entity_list_address, index)
            chunk = memfuncs.ProcMemHandler.ReadPointer(processHandle, chunk_address)
            if not is_valid_address(chunk):
                continue

            controller = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, entity_list.entity_slot_address(chunk, index)
            )
            if not is_valid_address(controller):
                continue

            pawn_handle = memfuncs.ProcMemHandler.ReadInt(
                processHandle, controller + Offsets.offset.m_hPlayerPawn
            )
            if not pawn_handle:
                continue

            pawn_chunk = memfuncs.ProcMemHandler.ReadPointer(
                processHandle,
                entity_list.entity_list_chunk_address(entity_list_address, pawn_handle),
            )
            if not is_valid_address(pawn_chunk):
                continue

            pawn = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, entity_list.entity_slot_address(pawn_chunk, pawn_handle)
            )
            if not is_valid_address(pawn) or pawn == LocalPlayer.pawnAddress:
                continue

            scene_node = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, pawn + Offsets.offset.m_pGameSceneNode
            )
            if not is_valid_address(scene_node):
                continue
            bone_matrix = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, scene_node + Offsets.offset.m_modelState + 0x80
            )
            if not is_valid_address(bone_matrix):
                continue

            entity.HeadPos = memfuncs.ProcMemHandler.ReadVec(
                processHandle, bone_matrix + AimBoneID * 32
            )
            entity.origin = memfuncs.ProcMemHandler.ReadVec(
                processHandle, pawn + Offsets.offset.m_vOldOrigin
            )
            view_matrix = memfuncs.ProcMemHandler.ReadMatrix(
                processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix
            )
            entity.head2d = calculations.world_to_screen(view_matrix, entity.HeadPos)
            entity.pixelDistance = calculations.distance_vec2(
                entity.head2d,
                Vector2(globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT / 2),
            )
            if entity.pixelDistance >= Options["AimbotFOV"]:
                continue

            entity.Distance = calculations.distance_vec3(entity.origin, LocalPlayer.origin)
            spotted = memfuncs.ProcMemHandler.ReadInt(
                processHandle,
                pawn + Offsets.offset.m_entitySpottedState + Offsets.offset.m_bSpotted,
            )
            team = memfuncs.ProcMemHandler.ReadInt(
                processHandle, pawn + Offsets.offset.m_iTeamNum
            )

            if Options["EnableAimbotVisibilityCheck"] and not spotted:
                continue
            if Options["EnableAimbotTeamCheck"] and LocalPlayer.Team == team:
                continue

            entities.append(entity)
        except pymem.exception.MemoryReadError as error:
            logutil.debug(f"[aimbot] entity {index} memory read failed: {error}")
        except (TypeError, ValueError, AttributeError) as error:
            logutil.debug(f"[aimbot] entity {index} data was invalid: {error}")

    return entities


def ResolveBoneToID(selected_position):
    """Compatibility wrapper for callers using the legacy function name."""
    return aim_settings.resolve_aim_bone_id(selected_position)


_last_update_time = time.perf_counter()


def Aimbot_Update(processHandle, clientBaseAddress, Offsets, Options, ARDUINO_HANDLE):
    tick_interval = 0.015625
    global _last_update_time

    try:
        current_time = time.perf_counter()
        frame_time = current_time - _last_update_time
        _last_update_time = current_time

        local_state = player_resolver.resolve_local_player(
            processHandle, clientBaseAddress, Offsets.offset
        )
        if local_state is None:
            return
        local_pawn = local_state.pawn
        local_controller = local_state.controller
        entity_list_address = local_state.entity_list

        local_team = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_pawn + Offsets.offset.m_iTeamNum
        )
        local_origin = memfuncs.ProcMemHandler.ReadVec(
            processHandle, local_pawn + Offsets.offset.m_vOldOrigin
        )
        view_matrix = memfuncs.ProcMemHandler.ReadMatrix(
            processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix
        )
        aim_bone_id = ResolveBoneToID(Options.get("AimPosition", "Head"))
        best_entity_2d = None
        best_entity_3d = None
        best_metric = float("inf")

        from features.esp.visibility import resolve_local_index

        local_index = resolve_local_index(
            processHandle, entity_list_address, local_controller
        )

        for index in range(1, 65):
            try:
                chunk = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle,
                    entity_list.entity_list_chunk_address(entity_list_address, index),
                )
                if not is_valid_address(chunk):
                    continue

                controller = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, entity_list.entity_slot_address(chunk, index)
                )
                if not is_valid_address(controller):
                    continue

                pawn_handle = memfuncs.ProcMemHandler.ReadInt(
                    processHandle, controller + Offsets.offset.m_hPlayerPawn
                )
                if not pawn_handle:
                    continue

                pawn_chunk = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle,
                    entity_list.entity_list_chunk_address(entity_list_address, pawn_handle),
                )
                if not is_valid_address(pawn_chunk):
                    continue

                pawn = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, entity_list.entity_slot_address(pawn_chunk, pawn_handle)
                )
                if not is_valid_address(pawn) or pawn == local_pawn:
                    continue

                team = memfuncs.ProcMemHandler.ReadInt(
                    processHandle, pawn + Offsets.offset.m_iTeamNum
                )
                if Options.get("EnableAimbotTeamCheck", False) and team == local_team:
                    continue

                if Options.get("EnableAimbotVisibilityCheck", False) and local_index > 0:
                    spotted_mask = memfuncs.ProcMemHandler.ReadInt(
                        processHandle,
                        pawn
                        + Offsets.offset.m_entitySpottedState
                        + Offsets.offset.m_bSpottedByMask,
                    )
                    if not (
                        spotted_mask & (1 << (local_index - 1))
                        or spotted_mask & (1 << local_index)
                    ):
                        continue

                scene_node = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, pawn + Offsets.offset.m_pGameSceneNode
                )
                if not is_valid_address(scene_node):
                    continue
                bone_matrix = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, scene_node + Offsets.offset.m_modelState + 0x80
                )
                if not is_valid_address(bone_matrix):
                    continue

                head_position = memfuncs.ProcMemHandler.ReadVec(
                    processHandle, bone_matrix + aim_bone_id * 32
                )
                origin = memfuncs.ProcMemHandler.ReadVec(
                    processHandle, pawn + Offsets.offset.m_vOldOrigin
                )

                if Options.get("EnableAimbotPrediction", False):
                    prediction_time = tick_interval * (3.55 + max(0.0, frame_time / tick_interval))
                    target_velocity = memfuncs.ProcMemHandler.ReadVec(
                        processHandle, pawn + Offsets.offset.m_vecVelocity
                    )
                    local_velocity = memfuncs.ProcMemHandler.ReadVec(
                        processHandle, local_pawn + Offsets.offset.m_vecVelocity
                    )
                    head_position = Vector3(
                        head_position.x
                        + (target_velocity.x - local_velocity.x) * prediction_time,
                        head_position.y
                        + (target_velocity.y - local_velocity.y) * prediction_time,
                        head_position.z
                        + (target_velocity.z - local_velocity.z) * prediction_time,
                    )

                head_2d = calculations.world_to_screen(view_matrix, head_position)
                if head_2d.x <= -1 or head_2d.y <= -1:
                    continue

                pixel_distance = calculations.distance_vec2(
                    head_2d,
                    Vector2(globals.SCREEN_WIDTH / 2, globals.SCREEN_HEIGHT / 2),
                )
                if pixel_distance >= Options.get("AimbotFOV", 75):
                    continue

                metric = pixel_distance + calculations.distance_vec3(origin, local_origin)
                if metric < best_metric:
                    best_metric = metric
                    best_entity_2d = head_2d
                    best_entity_3d = head_position
            except pymem.exception.MemoryReadError as error:
                logutil.debug(f"[aimbot] entity {index} memory read failed: {error}")
            except (TypeError, ValueError, AttributeError) as error:
                logutil.debug(f"[aimbot] entity {index} data was invalid: {error}")

        if best_entity_2d is None or best_entity_3d is None:
            return

        shots_fired = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_pawn + Offsets.offset.m_iShotsFired
        )
        if shots_fired > 1 and Options.get("EnableRecoilControl", False):
            globals.RCS_CTRL_BY_AIMBOT = True
            aim_punch_services = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, local_pawn + Offsets.offset.m_pAimPunchServices
            )
            if aim_punch_services:
                punch_x = memfuncs.ProcMemHandler.ReadFloat(
                    processHandle, aim_punch_services + Offsets.offset.m_aimPunchAngle
                )
                punch_y = memfuncs.ProcMemHandler.ReadFloat(
                    processHandle, aim_punch_services + Offsets.offset.m_aimPunchAngle + 0x4
                )
                recoil_smoothing = max(
                    1.0,
                    min(float(Options.get("RecoilControlSmoothing", 1.0)), 3.0),
                )
                best_entity_2d.y -= punch_x * 12.0 / recoil_smoothing
                best_entity_2d.x += punch_y * 12.0 / recoil_smoothing

        current_mouse = gameinput.getCurrentMousePosition()
        sensitivity_base = memfuncs.ProcMemHandler.ReadPointer(
            processHandle, clientBaseAddress + Offsets.offset.dwSensitivity
        )
        if not is_valid_address(sensitivity_base):
            return
        sensitivity = max(
            0.001,
            memfuncs.ProcMemHandler.ReadFloat(
                processHandle,
                sensitivity_base + Offsets.offset.dwSensitivity_sensitivity,
            ),
        )
        smoothing = max(1.0, float(Options.get("AimbotSmoothing", 1.0)))
        next_position = Vector2(
            current_mouse.x
            + (best_entity_2d.x - globals.SCREEN_WIDTH / 2.0) / sensitivity / smoothing,
            current_mouse.y
            + (best_entity_2d.y - globals.SCREEN_HEIGHT / 2.0) / sensitivity / smoothing,
        )

        if ARDUINO_HANDLE is not None:
            gameinput.moveMouseToLocationArdunio(next_position, handle=ARDUINO_HANDLE)
        else:
            gameinput.moveMouseToLocation(next_position)
    except pymem.exception.MemoryReadError as error:
        logutil.debug(f"[aimbot] memory read failed: {error}")
    except (TypeError, ValueError, AttributeError) as error:
        logutil.error(f"[aimbot] invalid runtime data: {error}")
    finally:
        globals.RCS_CTRL_BY_AIMBOT = False
