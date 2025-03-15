# WorkdayTimer

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

[中文文档](README_CN.md)

## Python Environment Management

To avoid Python environment conflicts, it's recommended to use a virtual environment. Here are two common methods:

### Using venv (Python built-in)

1. Create virtual environment:
```bash
python -m venv .venv
```

2. Activate virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/macOS:
```bash
source .venv/bin/activate
```

3. Deactivate virtual environment:
```bash
deactivate
```

### Using Conda

1. Create new environment:
```bash
conda create -n workdaytimer python=3.8
```

2. Activate environment:
```bash
conda activate workdaytimer
```

3. Deactivate environment:
```bash
conda deactivate
```

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

1. The timer will appear as a small desktop timer in the top-right corner of your screen
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