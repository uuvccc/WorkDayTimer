from cx_Freeze import setup, Executable
import os
import sys

# 基础目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 依赖项
build_exe_options = {
    "packages": ["os", "sys", "datetime", "logging", "random", "requests", 
                 "win32gui", "win32con", "multiprocessing", "threading",
                 "PyQt5", "keyboard", "PIL"],
    "includes": ["xml.parsers.expat"],
    "include_files": [
        ("images", "images"),
        ("start_time.txt", "start_time.txt"),
        ("flexible_mode.txt", "flexible_mode.txt"),
    ],
    "excludes": [],
}

# 确定基础应用类型
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 无控制台窗口

# 可执行文件配置
executables = [
    Executable(
        "workday_timer.py",
        base=base,
        target_name="WorkDayTimer_cx.exe",
        icon="images\\icon.ico"
    )
]

# 安装配置
setup(
    name="WorkDayTimer",
    version="1.0.0",
    description="A desktop timer application for tracking work hours",
    options={"build_exe": build_exe_options},
    executables=executables
)
