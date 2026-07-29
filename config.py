import os
import sys
import json


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

# 统一配置文件（新）
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# 旧配置文件（向后兼容，逐步废弃）
FLEXIBLE_MODE_FILE = os.path.join(BASE_DIR, "flexible_mode.txt")
REMINDER_SETTINGS_FILE = os.path.join(BASE_DIR, "reminder_settings.txt")

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

# 默认设置
DEFAULT_SETTINGS = {
    "flexible_mode": False,
    "run_on_startup": False,
    "reminders": {
        "checkin_reminder": True,
        "job_record_reminder": True,
        "checkout_reminder": True,
    },
}


def _load_settings():
    """加载设置，优先从 settings.json，兼容旧 .txt 文件"""
    settings = DEFAULT_SETTINGS.copy()

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            settings.update(data)
            if "reminders" in data and isinstance(data["reminders"], dict):
                settings["reminders"] = {
                    **DEFAULT_SETTINGS["reminders"],
                    **data["reminders"],
                }
        except Exception:
            pass
    else:
        # 迁移旧配置文件 → settings.json
        migrated = False
        if os.path.exists(FLEXIBLE_MODE_FILE):
            try:
                with open(FLEXIBLE_MODE_FILE, "r") as f:
                    settings["flexible_mode"] = f.read().strip().lower() == "true"
                migrated = True
            except Exception:
                pass
        if os.path.exists(REMINDER_SETTINGS_FILE):
            try:
                with open(REMINDER_SETTINGS_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().lower() == "true"
                            if k in settings["reminders"]:
                                settings["reminders"][k] = v
                migrated = True
            except Exception:
                pass
        if migrated:
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    return settings


def save_reminder_settings(reminder_dict):
    """保存提醒设置（向后兼容旧版调用）"""
    _settings = _load_settings()
    _settings["reminders"].update(reminder_dict)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_settings, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# 加载到模块级变量（旧版兼容）
_settings = _load_settings()
isFLEXIBLE = _settings["flexible_mode"]
reminder_settings = _settings["reminders"]
