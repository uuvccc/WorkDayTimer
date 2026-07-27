import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

START_TIME_FILE = os.path.join(BASE_DIR, "start_time.txt")
LOG_FILE = os.path.join(BASE_DIR, "app.log")
ICON_FILE = os.path.join(BASE_DIR, "images", "icon.png")

DEFAULT_TIMER_IMAGE = os.path.join(BASE_DIR, "images", "timer1.png")
IMAGE_DIRECTORY = os.path.join(BASE_DIR, "images", "timers")

os.makedirs(os.path.dirname(DEFAULT_TIMER_IMAGE), exist_ok=True)
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

WINDOW_POSITION_X = 1650
WINDOW_POSITION_Y = 30
WINDOW_SIZE_WIDTH = 200
WINDOW_SIZE_HEIGHT = 200

DIALOG_POSITION_X = 700
DIALOG_POSITION_Y = 500
DIALOG_SIZE_WIDTH = 750
DIALOG_SIZE_HEIGHT = 550

JOB_DIALOG_SIZE_WIDTH = 900
JOB_DIALOG_SIZE_HEIGHT = 700

FLEXIBLE_MODE_FILE = os.path.join(BASE_DIR, "flexible_mode.txt")
REMINDER_SETTINGS_FILE = os.path.join(BASE_DIR, "reminder_settings.txt")

def read_flexible_mode():
    try:
        with open(FLEXIBLE_MODE_FILE, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False

isFLEXIBLE = read_flexible_mode()

def read_reminder_settings():
    default_settings = {
        'checkin_reminder': True,
        'job_record_reminder': True,
        'checkout_reminder': True
    }
    try:
        with open(REMINDER_SETTINGS_FILE, "r") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().lower() == "true"
                    if key in default_settings:
                        default_settings[key] = value
    except FileNotFoundError:
        save_reminder_settings(default_settings)
    return default_settings

def save_reminder_settings(settings):
    try:
        with open(REMINDER_SETTINGS_FILE, "w") as f:
            for key, value in settings.items():
                f.write(f"{key}={value}\n")
    except Exception as e:
        print(f"Error saving reminder settings: {e}")

reminder_settings = read_reminder_settings()