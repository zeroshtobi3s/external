import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class StopWaiting(Exception):
    pass


def load_process_watcher_module():
    fake_pymem = types.ModuleType("pymem")
    fake_pymem.Pymem = object
    fake_process = types.ModuleType("pymem.process")
    fake_process.module_from_name = lambda *_: None

    original_pymem = sys.modules.get("pymem")
    original_pymem_process = sys.modules.get("pymem.process")
    sys.modules["pymem"] = fake_pymem
    sys.modules["pymem.process"] = fake_process
    try:
        module_path = Path(__file__).parents[1] / "functions" / "process_watcher.py"
        module_spec = importlib.util.spec_from_file_location("process_watcher_test_module", module_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module
    finally:
        if original_pymem is None:
            sys.modules.pop("pymem", None)
        else:
            sys.modules["pymem"] = original_pymem
        if original_pymem_process is None:
            sys.modules.pop("pymem.process", None)
        else:
            sys.modules["pymem.process"] = original_pymem_process


class ProcessConnectorTests(unittest.TestCase):
    def setUp(self):
        self.process_watcher = load_process_watcher_module()

    def test_process_connection_waits_without_holding_the_connector_lock(self):
        connector = self.process_watcher.ProcessConnector("game.exe")
        expected_process = types.SimpleNamespace(process_handle=7)

        def wait_for_process():
            self.assertFalse(connector._lock.locked())
            return expected_process

        connector._wait_for_process = wait_for_process

        self.assertIs(expected_process, connector.ensure_process())

    def test_failed_module_lookup_is_rate_limited_before_retrying(self):
        connector = self.process_watcher.ProcessConnector("game.exe", poll_interval=0.25)
        connector.ensure_process = Mock(return_value=types.SimpleNamespace(process_handle=7))
        connector.invalidate = Mock()
        self.process_watcher.module_from_name = Mock(side_effect=RuntimeError("disconnected"))

        with patch.object(
            self.process_watcher.time, "sleep", side_effect=StopWaiting
        ) as sleep, self.assertRaises(StopWaiting):
            connector._wait_for_module("client.dll")

        connector.invalidate.assert_called_once()
        sleep.assert_called_once_with(0.25)


if __name__ == "__main__":
    unittest.main()
