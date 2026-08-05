import os
import sys


def get_base_dir():
    """可写文件目录（settings.json / start_time.txt / app.log 等）。
    冻结（PyInstaller）时放在 exe 所在目录，保证配置持久化。"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_DIR = get_base_dir()


def get_resource_dir():
    """只读资源目录（images/）。
    PyInstaller --onefile 会把 --add-data 的图片解压到 sys._MEIPASS 临时目录，
    而不是 exe 旁边，所以资源必须从 _MEIPASS 读取。"""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return BASE_DIR


RESOURCE_DIR = get_resource_dir()


def resolve_resource(rel_path):
    """解析资源文件路径：优先用可写目录（exe 旁 / 项目根）下用户放置的同名资源，
    找不到再回退到内置资源（_MEIPASS）。
    这样用户可以把自定义图片放到 exe 旁边的 images/ 文件夹里覆盖默认资源。"""
    local = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(local):
        return local
    return os.path.join(RESOURCE_DIR, rel_path)


def resolve_resource_dir(rel_path):
    """解析资源目录：优先用可写目录下已存在的同名目录，否则回退到内置目录。"""
    local = os.path.join(BASE_DIR, rel_path)
    if os.path.isdir(local):
        return local
    return os.path.join(RESOURCE_DIR, rel_path)


# 统一配置文件
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# 旧配置文件（用于迁移）
OLD_FLEXIBLE_MODE_FILE = os.path.join(BASE_DIR, "flexible_mode.txt")
OLD_REMINDER_SETTINGS_FILE = os.path.join(BASE_DIR, "reminder_settings.txt")

START_TIME_FILE = os.path.join(BASE_DIR, "start_time.txt")
LOG_FILE = os.path.join(BASE_DIR, "app.log")
ICON_FILE = resolve_resource("images/icon.png")

DEFAULT_TIMER_IMAGE = resolve_resource("images/timer1.png")
IMAGE_DIRECTORY = resolve_resource_dir("images/timers")

# 源码运行时保证图片目录存在；打包运行时图片由 --add-data 提供，无需创建
if not getattr(sys, 'frozen', False):
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
DEFAULT_CHECK_UPDATE_DELAY = 10
DEFER_UPDATE_DAYS = 7

# 默认设置
DEFAULT_SETTINGS = {
    "flexible_mode": False,
    "run_on_startup": False,
    "auto_check_update": True,
    "check_update_delay": DEFAULT_CHECK_UPDATE_DELAY,
    "defer_update_until": None,
    "work_hours": DEFAULT_WORK_HOURS,
    "fixed_start_hour": DEFAULT_FIXED_START_HOUR,
    "job_record_before_end_minutes": DEFAULT_JOB_RECORD_BEFORE_END_MINUTES,
    "reminders": {
        "checkin_reminder": True,
        "job_record_reminder": True,
        "checkout_reminder": True,
    },
}
