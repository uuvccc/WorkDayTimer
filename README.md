# MiniTools

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) [![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/uuvccc/WorkDayTimer/pulls) [![GitHub Actions CI](https://github.com/uuvccc/WorkDayTimer/workflows/Python%20application/badge.svg)](https://github.com/uuvccc/WorkDayTimer/actions) [![GitHub release](https://img.shields.io/github/v/release/uuvccc/WorkDayTimer)](https://github.com/uuvccc/WorkDayTimer/releases) [![GitHub all releases](https://img.shields.io/github/downloads/uuvccc/WorkDayTimer/total)](https://github.com/uuvccc/WorkDayTimer/releases) [![GitHub issues](https://img.shields.io/github/issues/uuvccc/WorkDayTimer)](https://github.com/uuvccc/WorkDayTimer/issues)

A desktop utility application for tracking work hours with reminder functionality.

## Features

- Automatic work hour tracking
- Check-in and check-out reminders
- Daily work log reminders
- System tray integration
- Customizable desktop timer display
- Flexible/Fixed time mode support
- Custom timer functionality
- Reminder settings configuration
- Auto-update capability
- Run on startup option

## Requirements

- Python 3.6 or higher
- PyQt5 >= 5.15.0
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/uuvccc/WorkDayTimer.git
cd WorkDayTimer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

You can run the application in two ways:

### Option 1: Run Python Script

```bash
python main.py
```

### Option 2: Run Executable

You can also run the pre-built executable file directly:

1. Download the latest release from the releases page
2. Extract the zip file
3. Run `MiniTools.exe`

After starting the application:

1. The timer will appear as a small widget in the top-right corner of your screen
2. System tray icon provides quick access to:
   - Open the main window
   - Toggle flexible mode
   - Set custom timer
   - Open settings dialog
   - Update application
   - Toggle run on startup
   - Exit the application
3. Automatic reminders will notify you for:
   - Check-in time
   - Work log submission
   - Check-out time
   - System shutdown (in fixed time mode)

## Configuration

The application uses a configuration file for reminder settings. You can access the settings dialog through the system tray menu to:
- Enable/disable check-in reminder
- Enable/disable work record reminder
- Enable/disable check-out reminder

## Project Structure

```
WorkDayTimer/
├── main.py                    # Entry point
├── app/
│   ├── __init__.py
│   ├── application.py         # Application lifecycle management
│   ├── main_window.py         # Main window widget
│   ├── config/
│   │   ├── constants.py       # Configuration constants
│   │   └── manager.py         # Configuration manager class
│   ├── services/
│   │   ├── time_service.py    # Time calculation service
│   │   ├── system_service.py  # System operations (startup, shutdown, QQ toggle)
│   │   ├── update_service.py  # Application update service
│   │   └── keyboard_service.py# Keyboard hook service
│   ├── ui/
│   │   ├── tray_menu.py       # System tray menu
│   │   └── dialogs/
│   │       ├── settings_dialog.py      # Settings dialog
│   │       ├── custom_timer_dialog.py  # Custom timer dialog
│   │       └── reminder_dialog.py      # Reminder dialogs
│   └── utils/
│       ├── logger.py          # Logging utility
│       └── version.py         # Version comparison utility
├── tests/                     # Unit tests
├── images/                    # Timer images
├── requirements.txt           # Dependencies
├── setup.py                   # Package setup
└── workday_timer.spec         # PyInstaller configuration
```

## Building

To build the executable:

```bash
python workday_timer.spec
```

Or using PyInstaller directly:

```bash
pyinstaller --onefile --windowed --name MiniTools main.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details