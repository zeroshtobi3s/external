# NERON

External enhancement suite for Counter-Strike 2 featuring ESP overlay, aimbot, triggerbot, recoil control, FOV changer, bhop assist, spectator monitor.

> ⚠️ External cheats can violate Valve policies. Use at your own risk.

## Highlights
- ESP with boxes, skeletons, health, distance, bomb timer, spectator list.
- Aimbot with smoothing, prediction, recoil handoff, team/visibility checks, optional Arduino output.
- Triggerbot with anti-flash, standalone recoil control system, stream-proof toggle.
- DearPyGui UI with live configuration, stored automatically in `settings.json`.

## Gallery
<p align="center">
  <img src="/assets/tXZT1Ve.webp" alt="NERON ESP Overlay preview" width="720">
</p>
<p align="center">
  <img src="/assets/tXZT1Ve2.webp" alt="NERON DearPyGui control panel preview" width="720">
</p>

## Requirements

NERON is a **Windows-only** project. Run it on a supported 64-bit Windows environment with a compatible Python installation. The code imports Windows APIs through `pywin32`, so startup on Linux or macOS is not supported. The project also requires a locally running Counter-Strike 2 session; without it, the connector intentionally waits for `cs2.exe` and `client.dll`.

## Quick Start
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

1. Launch CS2 and join a session.
2. Run `python main.py` from the repository root. Administrator privileges may be required by the platform APIs.
3. NERON waits for `cs2.exe`/`client.dll`, then starts the GUI, overlay, and worker threads.

Settings are stored as `settings.json` alongside `main.py`, regardless of the directory from which the command is launched. Existing settings files are merged with newly introduced default settings so upgrades do not fail because a key is missing.

## Hotkeys
- `End` — terminate NERON.
- `Insert` — toggle GUI visibility.
- `Home` — toggle stream-proof mode for GUI and ESP overlay.

Additional keybinds (aimbot, triggerbot, etc.) are configurable inside the GUI.

Offsets are fetched at runtime from the CS2 dumper repo; if the request fails, provide manual dumps under `output/`. Enable verbose logging with `NERON_DEBUG=1`.

## License & Credits
Crafted by [SadraKhorami](https://github.com/SadraKhorami). Visit the official site: [khorami.dev](https://khorami.dev). If this project helps you, please star the repository to support ongoing work.

## Development checks

Run the following commands from the repository root before opening a pull request. The unit tests cover configuration persistence, offset cache fallback, entity-list address calculation, aim-position mapping, and process reconnection behavior without requiring a running game session.

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
```

Continuous integration runs the same syntax and unit-test checks on `windows-latest` for pushes and pull requests.

### Runtime diagnostics

If a feature does not respond during a Windows smoke test, run the application from PowerShell with debug output enabled and retain the complete console output:

```powershell
$env:NERON_DEBUG = "1"
python main.py
```

The local-player resolver reports only when its resolution source changes. A line such as `[player-resolver] resolved via controller-handle` confirms that the shared memory acquisition path is available; `[player-resolver] local pawn could not be resolved` indicates that the console output should be attached to the bug report.
