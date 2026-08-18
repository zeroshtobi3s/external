import importlib.util
import unittest
from pathlib import Path


def load_entity_list_module():
    module_path = Path(__file__).parents[1] / "features" / "esp" / "entity_list.py"
    module_spec = importlib.util.spec_from_file_location("esp_entity_list_test_module", module_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


ENTITY_LIST = load_entity_list_module()


class EntityListAddressTests(unittest.TestCase):
    def test_chunk_address_uses_masked_handle_and_chunk_index(self):
        entity_list_address = 0x100000
        handle = 0x40001234

        result = ENTITY_LIST.entity_list_chunk_address(entity_list_address, handle)

        expected = entity_list_address + ENTITY_LIST.ENTITY_LIST_CHUNK_POINTER_STRIDE * ((handle & 0x7FFF) >> 9)
        expected += ENTITY_LIST.ENTITY_LIST_CHUNK_OFFSET
        self.assertEqual(expected, result)

    def test_controller_slot_uses_cs2_entity_stride(self):
        chunk_address = 0x500000
        controller_index = 64

        result = ENTITY_LIST.entity_slot_address(chunk_address, controller_index)

        self.assertEqual(chunk_address + 0x78 * controller_index, result)
        self.assertEqual(0x78, ENTITY_LIST.ENTITY_LIST_ENTRY_STRIDE)

    def test_pawn_handle_uses_only_the_slot_bits(self):
        chunk_address = 0x600000
        pawn_handle = 0xABCD1234

        result = ENTITY_LIST.entity_slot_address(chunk_address, pawn_handle)

        self.assertEqual(chunk_address + 0x78 * (pawn_handle & 0x1FF), result)


if __name__ == "__main__":
    unittest.main()
