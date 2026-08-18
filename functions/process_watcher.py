import threading
import time
from collections.abc import Iterable

import pymem
from pymem.process import module_from_name

from functions import logutil


class ProcessConnector:
    def __init__(
        self,
        process_name: str,
        modules: Iterable[str] | None = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.process_name = process_name
        self.poll_interval = max(0.1, float(poll_interval))
        self._lock = threading.Lock()
        self._proc: pymem.Pymem | None = None
        self._module_cache: dict[str, int] = {}
        self._module_whitelist = {m.lower() for m in modules} if modules else set()

    def _wait_for_process(self) -> pymem.Pymem:
        while True:
            try:
                proc = pymem.Pymem(self.process_name)
                return proc
            except Exception:  # noqa: BLE001 - pymem errors differ across supported Windows versions.
                logutil.debug(f"[proc] waiting for process {self.process_name} ...")
                time.sleep(self.poll_interval)

    def _wait_for_module(self, module_name: str) -> int:
        while True:
            proc = self.ensure_process()
            try:
                module = module_from_name(proc.process_handle, module_name)
                if module:
                    return module.lpBaseOfDll
            except Exception as error:  # noqa: BLE001 - module reads expose platform-specific pymem errors.
                self.invalidate()
                logutil.debug(f"[proc] module lookup failed for {module_name}: {error}")
                time.sleep(self.poll_interval)
                continue

            logutil.debug(f"[proc] waiting for module {module_name} ...")
            time.sleep(self.poll_interval)

    def ensure_process(self) -> pymem.Pymem:
        with self._lock:
            proc = self._proc

        if proc is not None:
            try:
                _ = proc.process_handle
                return proc
            except Exception:  # noqa: BLE001 - a stale process handle has no stable shared exception type.
                self.invalidate()

        connected_proc = self._wait_for_process()
        with self._lock:
            if self._proc is None:
                self._proc = connected_proc
                self._module_cache.clear()
            return self._proc

    def ensure_module(self, module_name: str) -> int:
        key = module_name.lower()
        with self._lock:
            cached = self._module_cache.get(key)
            if cached:
                return cached

        base = self._wait_for_module(module_name)
        with self._lock:
            self._module_cache[key] = base
        return base

    def invalidate(self) -> None:
        with self._lock:
            self._proc = None
            self._module_cache.clear()

    def process_handle(self) -> pymem.Pymem:
        return self.ensure_process()

    def module_base(self, module_name: str) -> int:
        return self.ensure_module(module_name)
