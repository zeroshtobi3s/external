"""Persistent settings helpers with schema-preserving defaults."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from functions import logutil


def _as_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def save_settings(settings: Mapping[str, Any], path: str | Path) -> bool:
    """Atomically persist *settings* and keep the previous file on write failure."""
    destination = _as_path(path)
    temporary_name: str | None = None

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(dict(settings), temporary_file, indent=4, sort_keys=True)
            temporary_file.write("\n")
            temporary_name = temporary_file.name
        os.replace(temporary_name, destination)
        return True
    except (OSError, TypeError, ValueError) as error:
        logutil.error(f"[config] could not save settings to {destination}: {error}")
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass
        return False


def load_settings(defaults: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    """Load stored settings while retaining newly introduced default keys.

    Invalid or unavailable files return a fresh copy of *defaults*. A missing file
    is initialized immediately so a first launch has a visible, editable config.
    """
    destination = _as_path(path)
    merged = deepcopy(dict(defaults))

    if not destination.exists():
        save_settings(merged, destination)
        return merged

    try:
        with destination.open("r", encoding="utf-8") as settings_file:
            loaded = json.load(settings_file)
    except (OSError, json.JSONDecodeError) as error:
        logutil.error(f"[config] could not load settings from {destination}: {error}")
        return merged

    if not isinstance(loaded, dict):
        logutil.error(
            f"[config] expected an object in {destination}, got {type(loaded).__name__}; "
            "using defaults instead."
        )
        return merged

    merged.update(loaded)
    return merged
