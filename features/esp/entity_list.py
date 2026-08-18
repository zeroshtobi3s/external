"""Address helpers for the Counter-Strike 2 entity list used by ESP."""

from __future__ import annotations

ENTITY_LIST_CHUNK_OFFSET = 0x10
ENTITY_LIST_CHUNK_POINTER_STRIDE = 0x8
ENTITY_LIST_ENTRY_STRIDE = 0x78
ENTITY_INDEX_MASK = 0x7FFF
ENTITY_CHUNK_INDEX_SHIFT = 9
ENTITY_SLOT_MASK = 0x1FF


def entity_list_chunk_address(entity_list_address: int, entity_handle: int) -> int:
    """Return the address of the chunk that contains *entity_handle*."""
    index = entity_handle & ENTITY_INDEX_MASK
    return (
        entity_list_address
        + ENTITY_LIST_CHUNK_POINTER_STRIDE * (index >> ENTITY_CHUNK_INDEX_SHIFT)
        + ENTITY_LIST_CHUNK_OFFSET
    )


def entity_slot_address(chunk_address: int, entity_handle: int) -> int:
    """Return the address of an entity pointer within one entity-list chunk."""
    return chunk_address + ENTITY_LIST_ENTRY_STRIDE * (entity_handle & ENTITY_SLOT_MASK)
