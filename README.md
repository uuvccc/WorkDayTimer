# MiniTools

English | [简体中文](README_CN.md)

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](#requirements) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/uuvccc/WorkDayTimer/pulls) [![GitHub Actions CI](https://github.com/uuvccc/WorkDayTimer/workflows/Python%20application/badge.svg)](https://github.com/uuvccc/WorkDayTimer/actions) [![GitHub release](https://img.shields.io/github/v/release/uuvccc/WorkDayTimer)](https://github.com/uuvccc/WorkDayTimer/releases) [![GitHub all releases](https://img.shields.io/github/downloads/uuvccc/WorkDayTimer/total)](https://github.com/uuvccc/WorkDayTimer/releases) [![GitHub issues](https://img.shields.io/github/issues/uuvccc/WorkDayTimer)](https://github.com/uuvccc/WorkDayTimer/issues)

MiniTools is a Windows desktop-pet style workday tracker. It starts counting automatically, shows a frameless always-on-top countdown in the top-right corner of your screen, and reminds you at check-in, work-log, and check-out time. Windows only.

## Features

- **Automatic work-hour tracking** — starts counting as soon as the app launches; no manual start/stop.
- **Timed reminders** — check-in at startup, work-log submission before the day ends, and check-out when the workday is over.
- **Flexible / fixed work modes** — configurable daily work hours, or a fixed start time with an optional one-click shutdown at the end of the day.
- **Custom countdown timer** — pick 1–240 minutes and get a reminder when it expires.
- **Desktop pet** — 200×200 frameless, always-on-top, semi-transparent window with rotating timer images and 49 built-in ASCII animations.
- **Custom ASCII animations** — drop `.json` / `.txt` / `.ascii` files into the `ascii_animations/` folder next to the executable and reload them from the tray menu. See [ascii_animations/README.md](ascii_animations/README.md).
- **Live input feedback** — pressed keys and mouse buttons appear as a small bubble above the pet (can be disabled in settings).
- **System tray integration** — show the window, open the custom timer, manage animations, open settings, check for updates, or quit.
- **Global hotkey** — press `Enter` globally to toggle the QQ window.
- **Automatic updates** — incremental updates from GitHub Releases (file-level manifest + per-file `.gz` assets, falling back to the full zip).
- **Run on startup** — optional per-user registry entry.
- **Local-only data** — settings in `settings.json`, launch history in `start_time.txt`, logs in `logs/app.log`.

## Requirements

- Windows 10 or 11
- Python 3.10 or higher (only when running from source)
- PyQt5 >= 5.15.0
- Other dependencies listed in [requirements.txt](requirements.txt)

## Installation

### Pre-built executable (recommended)

1. Download the latest `MiniTools.zip` from the [releases page](https://github.com/uuvccc/WorkDayTimer/releases).
2. Extract it to a writable folder.
3. Run `MiniTools.exe`. Python is not required.

### From source

```bash
git clone https://github.com/uuvccc/WorkDayTimer.git
cd WorkDayTimer
pip install -r requirements.txt
python main.py
```

Using a virtual environment is recommended:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

After launching, the timer appears as a small pet in the top-right corner of the screen. Drag it anywhere you like, and right-click it to open the context menu.

The tray icon provides quick access to:

- Show Window
- Custom Timer…
- Custom Animations… (import help)
- Reload Animations (re-scan the `ascii_animations/` folder)
- Settings…
- Check for Updates…
- Quit

Automatic reminders cover:

- Check-in time (on first launch of the day)
- Work-log submission (configurable lead time before the end of the workday)
- Check-out time
- System shutdown (fixed mode only)

## Configuration

Runtime configuration is stored in `settings.json` next to the executable (or at the project root when running from source). Use the tray menu → **Settings…** to change:

- Flexible work hours on/off, daily work hours, fixed-mode start time
- Work-log reminder lead time (minutes before the end of the workday)
- Dialog style (native Windows vs. card)
- Input-feedback bubbles on/off
- Check-in / work-log / check-out reminders on/off
- Start MiniTools automatically when you log in
- Automatic update checks and the delay before checking

Old `flexible_mode.txt` / `reminder_settings.txt` files are migrated into `settings.json` automatically on startup.

## Project Structure

```
WorkDayTimer/
├── main.py                          # Entry point
├── build.py                         # Nuitka build + release packaging
├── app/
│   ├── __init__.py                  # __version__
│   ├── application.py               # QApplication lifecycle & exception handling
│   ├── main_window.py               # Core coordinator: services, timers, pet UI
│   ├── config/
│   │   ├── constants.py             # Path resolution & default settings
│   │   └── manager.py               # JSON config manager (module-level singleton)
│   ├── services/
│   │   ├── time_service.py          # Work-hour calculation, start_time.txt
│   │   ├── system_service.py        # Startup registry, QQ window toggle, shutdown
│   │   ├── update_service.py        # GitHub update check, incremental download, updater
│   │   ├── keyboard_service.py      # Global Enter-key hook
│   │   └── feedback_service.py      # Global keyboard/mouse hooks for pet feedback
│   ├── ui/
│   │   ├── ascii_art.py             # ASCII scene loading & rendering
│   │   ├── tray_menu.py             # System tray icon and menu
│   │   └── dialogs/
│   │       ├── common.py            # Shared native dialog helpers
│   │       ├── custom_ascii_help.py # Custom animation import help
│   │       ├── custom_timer_dialog.py
│   │       ├── reminder_dialog.py
│   │       └── settings_dialog.py
│   └── utils/
│       ├── image.py                 # Transparency helpers (pure Python)
│       ├── logger.py                # File + console logging
│       └── version.py               # Semantic version comparison
├── tests/                           # Unit tests (unittest)
├── images/                          # Icons and timer images
├── ascii_animations/                # Built-in & user ASCII animations
├── docs/                            # Design docs and execution plans
├── .github/workflows/               # CI (lint/test/build) and auto-release
├── requirements.txt
├── settings.json                    # Created/updated at runtime
└── start_time.txt                   # Daily launch history
```

## Development

```bash
# Run from source
python main.py

# Run tests (from the project root)
python -m unittest discover tests -v

# Lint
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

## Building

Builds use [Nuitka](https://nuitka.net/) in standalone mode. `build.py` is the single build entry point for both local builds and CI — do not pass extra packaging flags on the command line.

```bash
pip install "nuitka>=2.4,<3"
python build.py
```

Artifacts in `dist/`:

- `MiniTools.zip` — full standalone package (extract and run `MiniTools.exe`)
- `MiniTools.manifest.json` — version, file sizes, and SHA-256 hashes for incremental updates
- `assets/*.gz` — one compressed asset per file, downloaded only when it differs from the local copy

## Updating

On startup (or from the tray menu), the app checks `api.github.com` directly for the latest release. It then:

1. Downloads `MiniTools.manifest.json` and compares local files by size and SHA-256.
2. Downloads only the changed per-file `.gz` assets, verifying each hash; otherwise falls back to the full `MiniTools.zip`.
3. Retries downloads through mirror proxies if direct GitHub access fails.
4. Writes an `updater.bat` that requests administrator rights, closes the running app, copies the staged files, and restarts it.

Versions are defined in [app/__init__.py](app/__init__.py); CI appends the commit count (e.g. `1.0.0.142`).

## Contributing

Contributions are welcome. Please open a Pull Request. For architecture and product context, see [ARCHITECTURE.md](ARCHITECTURE.md) and [PRODUCT_SENSE.md](PRODUCT_SENSE.md).

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
