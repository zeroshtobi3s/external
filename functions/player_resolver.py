"""Resilient resolution of the local player pawn from live CS2 memory."""

from __future__ import annotations

from dataclasses import dataclass

from functions import entity_list, logutil, memfuncs

MIN_VALID_ADDRESS = 0x10000
MAX_VALID_ADDRESS = 0x7FFFFFFFFFFF
_last_reported_status = None


def _report_status(status: str) -> None:
    """Emit one debug line whenever local-player resolution changes state."""
    global _last_reported_status
    if status != _last_reported_status:
        logutil.debug(f"[player-resolver] {status}")
        _last_reported_status = status


@dataclass(frozen=True)
class LocalPlayerState:
    pawn: int
    controller: int
    entity_list: int
    source: str


def is_valid_address(address: int | None) -> bool:
    return isinstance(address, int) and MIN_VALID_ADDRESS < address < MAX_VALID_ADDRESS


def resolve_entity_handle(process, entity_list_address: int, handle: int) -> int:
    """Resolve a CS2 entity handle to a validated entity pointer."""
    if not entity_list_address or not handle or handle == 0xFFFFFFFF:
        return 0
    try:
        chunk = memfuncs.ProcMemHandler.ReadPointer(
            process,
            entity_list.entity_list_chunk_address(entity_list_address, handle),
        )
        if not is_valid_address(chunk):
            return 0
        candidate = memfuncs.ProcMemHandler.ReadPointer(
            process,
            entity_list.entity_slot_address(chunk, handle),
        )
        return candidate if is_valid_address(candidate) else 0
    except Exception:  # noqa: BLE001 - memory-access errors differ by platform and process state.
        return 0


def _is_probable_pawn(process, pawn: int, offsets) -> bool:
    if not is_valid_address(pawn):
        return False
    try:
        health = memfuncs.ProcMemHandler.ReadInt(process, pawn + offsets.m_iHealth)
        return 0 <= health <= 100
    except Exception:  # noqa: BLE001 - invalid or stale pointers are expected during transitions.
        return False


def resolve_local_player(process, client_base_address: int, offsets) -> LocalPlayerState | None:
    """Resolve the local pawn using the most reliable sources available.

    The controller-to-handle route is preferred. Direct and handle interpretations
    of ``dwLocalPlayerPawn`` are retained as compatibility fallbacks for game
    states where one source is temporarily unavailable.
    """
    try:
        entity_list_address = memfuncs.ProcMemHandler.ReadPointer(
            process, client_base_address + offsets.dwEntityList
        )
        controller = memfuncs.ProcMemHandler.ReadPointer(
            process, client_base_address + offsets.dwLocalPlayerController
        )
    except Exception:  # noqa: BLE001 - process can close between two reads.
        return None

    if not is_valid_address(entity_list_address):
        _report_status("entity list is unavailable")
        return None

    if is_valid_address(controller):
        try:
            pawn_handle = memfuncs.ProcMemHandler.ReadInt(
                process, controller + offsets.m_hPlayerPawn
            )
        except Exception:  # noqa: BLE001 - stale controller reads are transient.
            pawn_handle = 0
        pawn = resolve_entity_handle(process, entity_list_address, pawn_handle)
        if _is_probable_pawn(process, pawn, offsets):
            state = LocalPlayerState(
                pawn, controller, entity_list_address, "controller-handle"
            )
            _report_status(f"resolved via {state.source}")
            return state

    direct_pawn = 0
    try:
        direct_pawn = memfuncs.ProcMemHandler.ReadPointer(
            process, client_base_address + offsets.dwLocalPlayerPawn
        )
    except Exception:  # noqa: BLE001 - direct pointer can be unavailable between map transitions.
        direct_pawn = 0
    if _is_probable_pawn(process, direct_pawn, offsets):
        state = LocalPlayerState(
            direct_pawn, controller or 0, entity_list_address, "direct-pointer"
        )
        _report_status(f"resolved via {state.source}")
        return state

    try:
        pawn_handle = memfuncs.ProcMemHandler.ReadInt(
            process, client_base_address + offsets.dwLocalPlayerPawn
        )
    except Exception:  # noqa: BLE001 - invalid local-player handle is a transient state.
        pawn_handle = 0
    pawn = resolve_entity_handle(process, entity_list_address, pawn_handle)
    if _is_probable_pawn(process, pawn, offsets):
        state = LocalPlayerState(
            pawn, controller or 0, entity_list_address, "offset-handle"
        )
        _report_status(f"resolved via {state.source}")
        return state

    _report_status("local pawn could not be resolved")
    return None
