from distutils.core import setup
import py2exe
import os
import sys

# 基础目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 配置选项
options = {
    "py2exe": {
        "compressed": True,
        "optimize": 2,
        "bundle_files": 3,  # 3 = 不打包 Python 解释器
        "includes": ["xml.parsers.expat", "sip"],
        "packages": ["os", "sys", "datetime", "logging", "random", "requests", 
                     "win32gui", "win32con", "multiprocessing", "threading",
                     "PyQt5", "keyboard", "PIL"],
    }
}

# 数据文件
data_files = [
    ("images", [os.path.join("images", f) for f in os.listdir("images") if os.path.isfile(os.path.join("images", f))]),
    ("", ["start_time.txt", "flexible_mode.txt"]),
]

# 可执行文件配置
setup(
    name="WorkDayTimer",
    version="1.0.0",
    description="A desktop timer application for tracking work hours",
    options=options,
    data_files=data_files,
    windows=[
        {
            "script": "workday_timer.py",
            "icon_resources": [(1, "images\\icon.ico")],
            "dest_base": "WorkDayTimer_py2exe"
        }
    ]
)
