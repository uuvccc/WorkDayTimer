import os
import sys

# Get the directory containing this script, compatible with both script and exe
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running in a normal Python environment
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# Path configurations
START_TIME_FILE = os.path.join(BASE_DIR, "start_time.txt")
LOG_FILE = os.path.join(BASE_DIR, "app.log")
ICON_FILE = os.path.join(BASE_DIR, "images", "icon.png")

# Image configurations
DEFAULT_TIMER_IMAGE = os.path.join(BASE_DIR, "images", "timer1.png")
IMAGE_DIRECTORY = os.path.join(BASE_DIR, "images", "timers")

# Create directories if they don't exist
os.makedirs(os.path.dirname(DEFAULT_TIMER_IMAGE), exist_ok=True)
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

# Window settings
WINDOW_POSITION_X = 1650
WINDOW_POSITION_Y = 30
WINDOW_SIZE_WIDTH = 200
WINDOW_SIZE_HEIGHT = 200

# Dialog settings
DIALOG_POSITION_X = 700
DIALOG_POSITION_Y = 500
DIALOG_SIZE_WIDTH = 750
DIALOG_SIZE_HEIGHT = 550

# Dialog settings for job record and checkin
JOB_DIALOG_SIZE_WIDTH = 900
JOB_DIALOG_SIZE_HEIGHT = 700

# Application settings
FLEXIBLE_MODE_FILE = os.path.join(BASE_DIR, "flexible_mode.txt")

# Read flexible mode from file
def read_flexible_mode():
    try:
        with open(FLEXIBLE_MODE_FILE, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False

isFLEXIBLE = read_flexible_mode()