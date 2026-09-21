# MSFS Diagnostics & Tuner

All-in-one desktop utility for **Microsoft Flight Simulator 2020 & 2024**. Auto-diagnoses crashes, resolves mod conflicts, reads your system hardware, and tunes your simulator graphics settings — all from a single dark-themed dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-GUI-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows&logoColor=white)

---

## Download

### Option 1: Download .exe (Recommended)
1. Go to [Releases](https://github.com/FreedomStrider39/MSFS-Diag-APP/releases)
2. Download `MSFS-Diagnostics.exe` from the latest release
3. Run it — no installation needed

### Option 2: Run from Source
```bash
git clone https://github.com/FreedomStrider39/MSFS-Diag-APP.git
cd MSFS-Diag-APP
pip install -r requirements.txt
python main.py
```

---

## Features

### System Dashboard
- Auto-detects your hardware (CPU, GPU, RAM, VRAM, monitor, refresh rate)
- Finds your MSFS installation (Steam, Microsoft Store, Xbox Game Pass, MSFS 2024)
- Detects your graphics tier (Low / Medium / High / Ultra)
- Shows admin rights status

### AI Crash Diagnostics
- Parses MSFS crash logs (`Events.xml`, `.log` files, Windows Event Viewer)
- **302+ known MSFS errors** across 34 categories — works offline, no API key needed
- **Web search fallback** — when error not in database, automatically searches flightsim.to forums, Reddit, and official support
- Optional **Groq cloud AI** (free Llama 3 70B, 30-second signup)
- Optional **Gemini cloud AI** (free Gemini 2.5 Flash, no credit card)
- AI priority: Groq > Gemini > Built-in rules + web search

### AI-Powered Config Tuning
- Analyzes your hardware, current settings, and crash history
- Returns personalized recommendations with reasoning
- 8 optimization presets: 60 FPS Competitive → VR 45 FPS Quality
- Applies MSFS graphics, NVIDIA Control Panel, Windows Power & Gaming settings
- **Automatic backup** before every change — one-click revert
- Never auto-applies — always shows preview first

### Mod Inspector
- Scans your Community folder for installed mods
- Detects mod sources (flightsim.to, Contrail, manual installs)
- Identifies potential mod conflicts and problematic add-ons

### Error Library
- Searchable database of 302+ MSFS errors
- Search by error name, DLL, error code, or symptom
- Filter by category and severity
- View detailed causes and step-by-step fixes
- Search online for any error with one click

### Settings
- Set Groq and Gemini API keys (both optional)
- Manual path configuration for MSFS and Community folders
- Re-detect paths automatically

---

## How It Works

```
Error reported (e.g. "nvlddmkm.dll crash")
        |
1. Check built-in database (302+ known errors)
   -> Found match? Return fixes immediately
        | (no match)
2. Search web automatically (DuckDuckGo, no key needed)
   -> Finds flightsim.to forums, Reddit, official support
        |
3. If Groq/Gemini available:
   -> Send error + web results to cloud AI for analysis
   -> AI synthesizes built-in knowledge + web solutions
        |
4. If no cloud AI:
   -> Return built-in fixes + web search results side-by-side
```

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
| requests | Cloud AI (Groq/Gemini, optional) |
| ddgs | Web search fallback (DuckDuckGo) |

---

## Building the .exe

```bash
pip install pyinstaller
pyinstaller build.spec
```

The standalone `.exe` will be in the `dist/` folder. No Python installation required for end users.

---

## Project Structure

```
MSFS-Diag-APP/
|-- main.py                    # Entry point
|-- build.spec                 # PyInstaller config
|-- requirements.txt
|-- pyproject.toml
|-- data/                      # User data (error library, backups)
|   +-- reverts/               # Automatic config backups
+-- src/
    +-- gui/
    |   |-- main_window.py     # Main application window
    |   |-- styles.py          # FlightSim.to-inspired dark theme
    |   +-- tabs/
    |       |-- dashboard_tab.py
    |       |-- config_tab.py
    |       |-- crash_tab.py
    |       |-- mods_tab.py
    |       |-- library_tab.py
    |       +-- settings_tab.py
    +-- services/
        |-- hardware.py        # System hardware detection
        |-- config_parser.py   # MSFS UserCfg.opt reader/writer
        |-- crash_reader.py    # Crash log parser
        |-- mod_scanner.py     # Community folder scanner
        |-- tuner.py           # Graphics config tuner
        |-- local_ai.py        # Offline AI diagnostics engine
        |-- error_library.py   # 302+ MSFS error database
        |-- ai_service.py      # Groq + Gemini cloud AI
        +-- web_search.py      # DuckDuckGo search fallback
```

---

## AI Setup (Optional)

The app works out of the box with the built-in rule engine. For better results, add a free API key:

### Groq (Best Quality)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign Up (free, no credit card, 30 seconds)
3. API Keys -> Create API Key -> Copy
4. In the app: Settings -> Paste key -> Save

### Gemini (Fast)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Get API key (free, no credit card)
3. In the app: Settings -> Paste key -> Save

---

## Contributing

Contributions are welcome! To add new MSFS errors to the built-in database:

1. Open the app -> Error Library tab
2. Note the error details (name, category, DLL, error code)
3. Edit `src/services/error_library.py` and add a new `ErrorEntry`
4. Submit a PR

---

## Disclaimer

This tool is not affiliated with Microsoft, Asobo Studio, or Microsoft Flight Simulator. Use at your own risk. 
---

## Support

- **Issues**: [GitHub Issues](https://github.com/FreedomStrider39/MSFS-Diag-APP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FreedomStrider39/MSFS-Diag-APP/discussions)

If this tool helps you, consider buying me a coffee!

[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?hosted_button_id=paypal.me/EtienneVerdet)
