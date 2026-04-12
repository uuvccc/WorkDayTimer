# WorkdayTimer

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) [![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/wasd845/WorkDayTimer/pulls) [![GitHub Actions CI](https://github.com/wasd845/WorkDayTimer/workflows/Python%20application/badge.svg)](https://github.com/wasd845/WorkDayTimer/actions) [![GitHub release](https://img.shields.io/github/v/release/wasd845/WorkDayTimer)](https://github.com/wasd845/WorkDayTimer/releases) [![GitHub all releases](https://img.shields.io/github/downloads/wasd845/WorkDayTimer/total)](https://github.com/wasd845/WorkDayTimer/releases) [![GitHub issues](https://img.shields.io/github/issues/wasd845/WorkDayTimer)](https://github.com/wasd845/WorkDayTimer/issues)

A desktop timer application for tracking work hours with reminder functionality.

## Features

- Automatic work hour tracking
- Check-in and check-out reminders
- Daily work log reminders
- System tray integration
- Customizable desktop timer display
- Flexible/Fixed time mode support

## Requirements

- Python 3.6 or higher
- PyQt5 >= 5.15.0
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/WorkDayTimer.git
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
python workday_timer.py
```

### Option 2: Run Executable

You can also run the pre-built executable file directly:

1. Download the latest release from the releases page
2. Extract the zip file
3. Run `workday_timer.exe`

After starting the application:

1. The timer will appear as a small widget in the top-right corner of your screen
2. System tray icon provides quick access to open/exit the application
3. Automatic reminders will notify you for:
   - Check-in time
   - Work log submission
   - Check-out time
   - System shutdown (in fixed time mode)

## Configuration

- `isFLEXIBLE`: Set to `True` for flexible work hours, `False` for fixed 9:00 AM start time
- Image paths can be customized in the code for different timer appearances
- Window position and size can be adjusted in the initialization parameters

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details