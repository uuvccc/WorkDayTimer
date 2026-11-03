import os
import sys


def is_packaged():
    """当前是否运行在打包后的 exe 中。

    Nuitka standalone 不设置 sys.frozen，而是在每个编译模块的 globals 里
    注入 __compiled__；PyInstaller 则设置 sys.frozen。两者都算打包模式。

    项目所有"源码 vs 打包"的分支判断都走这里，避免散落各处各写一份。
    utils 包禁止依赖 config，所以 logger.py 自维护等价副本。"""
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


def _get_exe_dir():
    """当前 exe 所在目录。

    打包模式：优先 sys.argv[0] 的父目录（Nuitka 下 sys.executable 是假的
    python.exe）；PyInstaller 等有 sys.frozen 的场景回退 sys.executable。
    源码模式：返回项目根目录（__file__ 向上两级）。"""
    if sys.argv and sys.argv[0]:
        argv0 = os.path.abspath(sys.argv[0])
        if is_packaged():
            # 打包：argv[0] 是真实 exe
            if argv0.lower().endswith(".exe") and os.path.isfile(argv0):
                return os.path.dirname(argv0)
            # fallback：PyInstaller 等设置了 sys.frozen 的场景
            return os.path.dirname(sys.executable)
        # 源码：argv[0] 一般是 main.py
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.dirname(sys.executable)


def get_base_dir():
    """可写文件目录（settings.json / start_time.txt / app.log 等）。
    打包后 = exe 所在目录；源码运行 = 项目根目录。"""
    return _get_exe_dir()


BASE_DIR = get_base_dir()


def get_exe_path():
    """当前运行的 exe 真实路径。

    Nuitka standalone 打包后 sys.executable 会指向 exe 目录下一个并不存在的
    python.exe，只有 sys.argv[0] 才是真实 exe；源码运行时 argv[0] 是 .py 文件，
    此时退回 sys.executable。"""
    if sys.argv and sys.argv[0]:
        argv0 = os.path.abspath(sys.argv[0])
        if argv0.lower().endswith(".exe") and os.path.isfile(argv0):
            return argv0
    return sys.executable


def get_resource_dir():
    """只读资源目录（images/、ascii_animations/ 等）。
    Nuitka standalone 下 --include-data-dir 把资源放在 exe 旁边，所以就是 exe 目录。"""
    return _get_exe_dir()


RESOURCE_DIR = get_resource_dir()


def resolve_resource(rel_path):
    """解析资源文件路径：优先用可写目录（exe 旁 / 项目根）下用户放置的同名资源，
    找不到再回退到内置资源。
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

IMAGE_DIRECTORY = resolve_resource_dir("images/timers")

# 源码运行时保证图片目录存在；打包运行时图片由 --include-data-dir 提供，无需创建
if not is_packaged():
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
    # 在宠物上方展示「按下的键 / 点击的鼠标按钮」气泡（默认开启，设置里可关）
    "show_input_feedback": True,
    # 对话框风格："windows"（原生标题栏，默认）/ "card"（彩色卡片）
    "dialog_style": "windows",
    "reminders": {
        "checkin_reminder": True,
        "job_record_reminder": True,
        "checkout_reminder": True,
    },
}
