# MSFS Diagnostics & Tuner

All-in-one desktop utility for **Microsoft Flight Simulator 2020 & 2024**. Auto-diagnoses crashes, resolves mod conflicts, reads your system hardware, and tunes your simulator graphics settings — all from a single dark-themed dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows&logoColor=white)

---

## Features

### System Dashboard
- Auto-detects your hardware (CPU, GPU, RAM, VRAM, display)
- Finds your MSFS installation (Steam, Microsoft Store, or custom path)
- Detects your graphics tier (Low / Medium / High / Ultra)

### AI Crash Diagnostics
- Parses MSFS crash logs (`Events.xml`, `.log` files, Windows Event Viewer)
- Built-in AI engine with **302+ known MSFS errors** across 34 categories — works offline, no API key needed
- Optional **Groq cloud AI** upgrade (free Llama 3 70B, 30-second signup, no credit card)

### Mod Inspector
- Scans your Community folder for installed mods
- Detects mod sources (flightsim.to, Contrail, manual installs)
- Identifies potential mod conflicts and problematic add-ons

### Config Tuner
- 8 optimization presets: 60 FPS Competitive, 60 FPS Balanced, 45 FPS Smooth, 30 FPS Quality, 30 FPS Ultra, VR 72 FPS, VR 45 FPS Quality, Auto-Detect
- Applies MSFS graphics settings, NVIDIA Control Panel, Windows Power & Gaming settings
- **Automatic backup** before every change — one-click revert
- Never auto-applies — all changes shown as preview first

### Extensible Error Library
- User-configurable: add, update, or remove custom error rules
- JSON persistence — your custom errors survive updates
- Searchable by keyword, error code, or category

---

## Screenshots

<!-- Add screenshots here -->
<!-- ![Dashboard](screenshots/dashboard.png) -->
<!-- ![Crash Diagnostics](screenshots/crash-diagnostics.png) -->
<!-- ![Config Tuner](screenshots/config-tuner.png) -->
<!-- ![Mod Inspector](screenshots/mod-inspector.png) -->

---

## Quick Start

### Option 1: Run from Source

```bash
git clone https://github.com/FreedomStrider39/MSFS-Diag-APP.git
cd MSFS-Diag-APP
pip install -r requirements.txt
python main.py
```

### Option 2: Download .exe (Coming Soon)

Download the latest release from [Releases](https://github.com/FreedomStrider39/MSFS-Diag-APP/releases) — no Python installation required.

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| OS | Windows 10/11 |
| MSFS | 2020 or 2024 |

### Python Dependencies

| Package | Purpose |
|---------|---------|
| PySide6 | GUI framework |
| psutil | System monitoring |
| wmi | Windows hardware info |
| requests | Cloud AI (optional) |

---

## Building the .exe

```bash
pip install pyinstaller
pyinstaller build.spec
```

The standalone `.exe` will be in the `dist/` folder.

---

## Project Structure

```
MSFS-Diag-APP/
├── main.py                    # Entry point
├── build.spec                 # PyInstaller config
├── requirements.txt
├── pyproject.toml
├── data/                      # User data (error library, backups)
│   └── reverts/               # Automatic config backups
└── src/
    ├── gui/
    │   ├── main_window.py     # Main application window
    │   ├── styles.py          # FlightSim.to-inspired dark theme
    │   └── tabs/
    │       ├── dashboard_tab.py
    │       ├── config_tab.py
    │       ├── crash_tab.py
    │       ├── mods_tab.py
    │       └── settings_tab.py
    └── services/
        ├── hardware.py        # System hardware detection
        ├── config_parser.py   # MSFS UserCfg.opt reader/writer
        ├── crash_reader.py    # Crash log parser
        ├── mod_scanner.py     # Community folder scanner
        ├── tuner.py           # Graphics config tuner
        ├── local_ai.py        # Offline AI diagnostics engine
        ├── error_library.py   # 302+ MSFS error database
        └── ai_service.py      # Optional Groq cloud AI
```

---

## Contributing

Contributions are welcome! To add new MSFS errors to the built-in database:

1. Open the app → Settings → Error Library
2. Add the error with category, severity, cause, and fixes
3. Or edit `src/services/error_library.py` directly and submit a PR

---

## Disclaimer

This tool is not affiliated with Microsoft, Asobo Studio, or Microsoft Flight Simulator. Use at your own risk. Always back up your settings before making changes.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/FreedomStrider39/MSFS-Diag-APP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FreedomStrider39/MSFS-Diag-APP/discussions)

If this tool helps you, consider buying me a coffee!

[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?hosted_button_id=YOUR_PAYPAL_ID)
