import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeMemory:
    def __init__(self, pointers=None, integers=None):
        self.pointers = pointers or {}
        self.integers = integers or {}

    def read_pointer(self, _process, address):
        return self.pointers.get(address, 0)

    def read_int(self, _process, address):
        return self.integers.get(address, 0)


def load_resolver(memory):
    fake_memfuncs = types.ModuleType("functions.memfuncs")
    fake_memfuncs.ProcMemHandler = type(
        "FakeProcMemHandler",
        (),
        {
            "ReadPointer": staticmethod(memory.read_pointer),
            "ReadInt": staticmethod(memory.read_int),
        },
    )
    fake_logutil = types.ModuleType("functions.logutil")
    fake_logutil.debug = lambda _message: None
    fake_entity_list = types.ModuleType("functions.entity_list")
    fake_entity_list.entity_list_chunk_address = (
        lambda base, handle: base + 0x8 * ((handle & 0x7FFF) >> 9) + 0x10
    )
    fake_entity_list.entity_slot_address = lambda chunk, handle: chunk + 0x78 * (handle & 0x1FF)
    fake_functions = types.ModuleType("functions")
    fake_functions.entity_list = fake_entity_list
    fake_functions.logutil = fake_logutil
    fake_functions.memfuncs = fake_memfuncs

    module_path = Path(__file__).parents[1] / "functions" / "player_resolver.py"
    module_spec = importlib.util.spec_from_file_location("player_resolver_test_module", module_path)
    module = importlib.util.module_from_spec(module_spec)
    previous_modules = {
        name: sys.modules.get(name)
        for name in (
            "functions",
            "functions.entity_list",
            "functions.logutil",
            "functions.memfuncs",
            module_spec.name,
        )
    }
    sys.modules["functions"] = fake_functions
    sys.modules["functions.entity_list"] = fake_entity_list
    sys.modules["functions.logutil"] = fake_logutil
    sys.modules["functions.memfuncs"] = fake_memfuncs
    sys.modules[module_spec.name] = module
    try:
        module_spec.loader.exec_module(module)
        return module
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


class PlayerResolverTests(unittest.TestCase):
    def setUp(self):
        self.client = 0x100000
        self.entity_list = 0x200000
        self.controller = 0x300000
        self.pawn = 0x400000
        self.handle = 3
        self.offsets = types.SimpleNamespace(
            dwEntityList=0x10,
            dwLocalPlayerController=0x18,
            dwLocalPlayerPawn=0x20,
            m_hPlayerPawn=0x30,
            m_iHealth=0x40,
            m_lifeState=0x44,
        )

    def test_controller_handle_route_has_priority(self):
        chunk = self.entity_list + 0x10
        pawn_slot = chunk + 0x78 * self.handle
        memory = FakeMemory(
            pointers={
                self.client + self.offsets.dwEntityList: self.entity_list,
                self.client + self.offsets.dwLocalPlayerController: self.controller,
                chunk: chunk,
                pawn_slot: self.pawn,
            },
            integers={
                self.controller + self.offsets.m_hPlayerPawn: self.handle,
                self.pawn + self.offsets.m_iHealth: 100,
                self.pawn + self.offsets.m_lifeState: 256,
            },
        )
        resolver = load_resolver(memory)

        state = resolver.resolve_local_player(object(), self.client, self.offsets)

        self.assertEqual(self.pawn, state.pawn)
        self.assertEqual(self.controller, state.controller)
        self.assertEqual("controller-handle", state.source)

    def test_direct_pointer_is_used_as_a_compatibility_fallback(self):
        memory = FakeMemory(
            pointers={
                self.client + self.offsets.dwEntityList: self.entity_list,
                self.client + self.offsets.dwLocalPlayerPawn: self.pawn,
            },
            integers={
                self.pawn + self.offsets.m_iHealth: 88,
                self.pawn + self.offsets.m_lifeState: 256,
            },
        )
        resolver = load_resolver(memory)

        state = resolver.resolve_local_player(object(), self.client, self.offsets)

        self.assertEqual(self.pawn, state.pawn)
        self.assertEqual("direct-pointer", state.source)

    def test_invalid_memory_returns_none_without_raising(self):
        resolver = load_resolver(FakeMemory())

        self.assertIsNone(resolver.resolve_local_player(object(), self.client, self.offsets))


if __name__ == "__main__":
    unittest.main()
