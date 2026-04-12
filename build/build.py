#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil

# 基础目录
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# 颜色输出
def print_color(text, color='green'):
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, 'reset')}{text}{colors['reset']}")

# 安装依赖
def install_dependencies():
    print_color("安装打包依赖...", 'blue')
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "cx-Freeze"], 
                      check=True, capture_output=True, text=True)
        print_color("依赖安装成功", 'green')
    except subprocess.CalledProcessError as e:
        print_color(f"依赖安装失败: {e.stderr}", 'red')
        sys.exit(1)

# 清理构建目录
def clean_build():
    print_color("清理构建目录...", 'blue')
    # 只清理dist目录，保留build目录中的配置文件
    build_dirs = ['dist']
    for dir_name in build_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print_color(f"清理 {dir_name} 目录成功", 'green')
            except Exception as e:
                print_color(f"清理 {dir_name} 目录失败: {e}", 'red')
    
    # 清理build目录中的临时文件，但保留配置文件
    build_dir = os.path.join(base_dir, 'build')
    if os.path.exists(build_dir):
        for item in os.listdir(build_dir):
            item_path = os.path.join(build_dir, item)
            # 只清理pycache目录，保留其他所有文件和目录
            if os.path.isdir(item_path) and item == '__pycache__':
                try:
                    shutil.rmtree(item_path)
                    print_color(f"清理 {item} 目录成功", 'green')
                except Exception as e:
                    print_color(f"清理 {item} 目录失败: {e}", 'red')

# 使用PyInstaller打包
def build_with_pyinstaller():
    print_color("使用 PyInstaller 打包...", 'blue')
    # 直接使用命令行参数，不使用spec文件
    try:
        # 构建命令参数
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", "WorkDayTimer",
            "--icon", "images/icon.ico",
            "--add-data", "images;images",
            "--add-data", "start_time.txt;.",
            "--add-data", "flexible_mode.txt;.",
            "--hidden-import", "xml.parsers.expat",
            "--hidden-import", "pkg_resources",
            "--hidden-import", "plistlib",
            "workday_timer/main.py"
        ]
        
        # 执行打包命令
        result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_color("PyInstaller 打包成功", 'green')
            # 复制可执行文件到根目录
            dist_exe = os.path.join(base_dir, 'dist', 'WorkDayTimer.exe')
            if os.path.exists(dist_exe):
                shutil.copy2(dist_exe, os.path.join(base_dir, 'WorkDayTimer.exe'))
                print_color("可执行文件已复制到根目录", 'green')
            else:
                print_color("可执行文件未生成", 'red')
        else:
            print_color(f"PyInstaller 打包失败: {result.stderr}", 'red')
    except Exception as e:
        print_color(f"PyInstaller 打包出错: {e}", 'red')

# 使用cx-Freeze打包
def build_with_cx_freeze():
    print_color("使用 cx-Freeze 打包...", 'blue')
    setup_file = os.path.join(base_dir, 'build', 'setup_cx.py')
    try:
        result = subprocess.run([sys.executable, setup_file, "build_exe"], 
                              cwd=base_dir, capture_output=True, text=True)
        if result.returncode == 0:
            print_color("cx-Freeze 打包成功", 'green')
            # 复制可执行文件到根目录
            build_exe_dir = os.path.join(base_dir, 'build', 'exe.win-amd64-3.13')
            if os.path.exists(build_exe_dir):
                cx_exe = os.path.join(build_exe_dir, 'WorkDayTimer_cx.exe')
                if os.path.exists(cx_exe):
                    shutil.copy2(cx_exe, os.path.join(base_dir, 'WorkDayTimer_cx.exe'))
                    print_color("cx-Freeze 可执行文件已复制到根目录", 'green')
        else:
            print_color(f"cx-Freeze 打包失败: {result.stderr}", 'red')
    except Exception as e:
        print_color(f"cx-Freeze 打包出错: {e}", 'red')

# 主函数
def main():
    print_color("WorkDayTimer 打包脚本", 'yellow')
    print_color("=" * 50, 'yellow')
    
    # 清理构建目录
    clean_build()
    
    # 安装依赖
    install_dependencies()
    
    # 非交互式模式，默认使用 PyInstaller 打包
    print_color("使用默认打包方式: PyInstaller", 'blue')
    build_with_pyinstaller()
    
    print_color("=" * 50, 'yellow')
    print_color("打包完成！", 'green')

if __name__ == '__main__':
    main()
