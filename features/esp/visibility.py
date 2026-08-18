from functions import memfuncs

from .entity_list import entity_list_chunk_address, entity_slot_address


def resolve_local_index(processHandle, EntityList, local_controller_addr) -> int:
    try:
        for i in range(1, 65):
            chunk_address = entity_list_chunk_address(EntityList, i)
            list_entry = memfuncs.ProcMemHandler.ReadPointer(processHandle, chunk_address)
            if not list_entry:
                continue
            controller = memfuncs.ProcMemHandler.ReadPointer(
                processHandle, entity_slot_address(list_entry, i)
            )
            if controller == local_controller_addr:
                return i
    except Exception:
        return 0
    return 0


def is_visible_to_local(processHandle, pawn, Offsets, local_index: int) -> bool:
    try:
        if local_index > 0:
            base = pawn + Offsets.offset.m_entitySpottedState
            mask = memfuncs.ProcMemHandler.ReadInt(processHandle, base + Offsets.offset.m_bSpottedByMask)
            return bool(mask & (1 << (local_index - 1))) or bool(mask & (1 << local_index))
    except Exception:
        return False
    return False

