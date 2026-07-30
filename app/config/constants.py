import os
import sys


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_DIR = get_base_dir()

# 统一配置文件
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# 旧配置文件（用于迁移）
OLD_FLEXIBLE_MODE_FILE = os.path.join(BASE_DIR, "flexible_mode.txt")
OLD_REMINDER_SETTINGS_FILE = os.path.join(BASE_DIR, "reminder_settings.txt")

START_TIME_FILE = os.path.join(BASE_DIR, "start_time.txt")
LOG_FILE = os.path.join(BASE_DIR, "app.log")
ICON_FILE = os.path.join(BASE_DIR, "images", "icon.png")

DEFAULT_TIMER_IMAGE = os.path.join(BASE_DIR, "images", "timer1.png")
IMAGE_DIRECTORY = os.path.join(BASE_DIR, "images", "timers")

os.makedirs(os.path.dirname(DEFAULT_TIMER_IMAGE), exist_ok=True)
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

WINDOW_SIZE_WIDTH = 200
WINDOW_SIZE_HEIGHT = 200

DIALOG_POSITION_X = 700
DIALOG_POSITION_Y = 500
DIALOG_SIZE_WIDTH = 750
DIALOG_SIZE_HEIGHT = 550

JOB_DIALOG_SIZE_WIDTH = 900
JOB_DIALOG_SIZE_HEIGHT = 700

# 工作时长默认值
DEFAULT_WORK_HOURS = 8.5
DEFAULT_FIXED_START_HOUR = 9.0
DEFAULT_JOB_RECORD_BEFORE_END_MINUTES = 60

# 默认设置
DEFAULT_SETTINGS = {
    "flexible_mode": False,
    "run_on_startup": False,
    "work_hours": DEFAULT_WORK_HOURS,
    "fixed_start_hour": DEFAULT_FIXED_START_HOUR,
    "job_record_before_end_minutes": DEFAULT_JOB_RECORD_BEFORE_END_MINUTES,
    "reminders": {
        "checkin_reminder": True,
        "job_record_reminder": True,
        "checkout_reminder": True,
    },
}
