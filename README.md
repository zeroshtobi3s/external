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

## Quick Start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyMeow
```
1. Launch CS2 and join a session.
2. Run `python main.py` (recommended with admin privileges).
3. NERON waits for `cs2.exe`/`client.dll`, then spawns the GUI, overlay, and worker threads.

## Hotkeys
- `End` — terminate NERON.
- `Insert` — toggle GUI visibility.
- `Home` — toggle stream-proof mode for GUI and ESP overlay.

Additional keybinds (aimbot, triggerbot, etc.) are configurable inside the GUI.

Offsets are fetched at runtime from the CS2 dumper repo; if the request fails, provide manual dumps under `output/`. Enable verbose logging with `NERON_DEBUG=1`.

## License & Credits
Crafted by [SadraKhorami](https://github.com/SadraKhorami). Visit the official site: [khorami.dev](https://khorami.dev). If this project helps you, please star the repository to support ongoing work.
