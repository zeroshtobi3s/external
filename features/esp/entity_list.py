"""Compatibility exports for ESP entity-list address helpers."""

from functions.entity_list import (
    ENTITY_CHUNK_INDEX_SHIFT,
    ENTITY_INDEX_MASK,
    ENTITY_LIST_CHUNK_OFFSET,
    ENTITY_LIST_CHUNK_POINTER_STRIDE,
    ENTITY_LIST_ENTRY_STRIDE,
    ENTITY_SLOT_MASK,
    entity_list_chunk_address,
    entity_slot_address,
)

__all__ = [
    "ENTITY_CHUNK_INDEX_SHIFT",
    "ENTITY_INDEX_MASK",
    "ENTITY_LIST_CHUNK_OFFSET",
    "ENTITY_LIST_CHUNK_POINTER_STRIDE",
    "ENTITY_LIST_ENTRY_STRIDE",
    "ENTITY_SLOT_MASK",
    "entity_list_chunk_address",
    "entity_slot_address",
]
