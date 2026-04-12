#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil

# Base directory
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Color output
def print_color(text, color='green'):
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    try:
        print(f"{colors.get(color, 'reset')}{text}{colors['reset']}")
    except UnicodeEncodeError:
        # Handle encoding issues on Windows
        # Remove color codes and print
        import re
        plain_text = re.sub(r'\033\[[0-9;]+m', '', text)
        print(plain_text)

# Install dependencies
def install_dependencies():
    print_color("Installing build dependencies...", 'blue')
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "cx-Freeze"], 
                      check=True, capture_output=True, text=True)
        print_color("Dependencies installed successfully", 'green')
    except subprocess.CalledProcessError as e:
        print_color(f"Failed to install dependencies: {e.stderr}", 'red')
        sys.exit(1)

# Clean build directories
def clean_build():
    print_color("Cleaning build directories...", 'blue')
    # Clean dist directory
    build_dirs = ['dist']
    for dir_name in build_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print_color(f"Cleaned {dir_name} directory successfully", 'green')
            except Exception as e:
                print_color(f"Failed to clean {dir_name} directory: {e}", 'red')
    
    # Clean pycache directories everywhere
    for root, dirs, files in os.walk(base_dir):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print_color(f"Cleaned {dir_path} directory successfully", 'green')
                except Exception as e:
                    print_color(f"Failed to clean {dir_path} directory: {e}", 'red')

# Build with PyInstaller
def build_with_pyinstaller():
    print_color("Building with PyInstaller...", 'blue')
    # Use command line parameters directly, not spec file
    try:
        # Build command parameters
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
            "--hidden-import", "PyQt5",
            "--hidden-import", "PyQt5.QtCore",
            "--hidden-import", "PyQt5.QtGui",
            "--hidden-import", "PyQt5.QtWidgets",
            "--hidden-import", "keyboard",
            "--hidden-import", "PIL",
            "--hidden-import", "requests",
            "--hidden-import", "numpy",
            "--hidden-import", "pywin32",
            "workday_timer/main.py"
        ]
        
        # Execute build command
        print_color(f"Running command: {' '.join(cmd)}", 'blue')
        result = subprocess.run(cmd, cwd=base_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print_color("PyInstaller build successful", 'green')
            # Copy executable to root directory
            dist_exe = os.path.join(base_dir, 'dist', 'WorkDayTimer.exe')
            if os.path.exists(dist_exe):
                shutil.copy2(dist_exe, os.path.join(base_dir, 'WorkDayTimer.exe'))
                print_color("Executable copied to root directory", 'green')
                # Verify the executable exists
                if os.path.exists(os.path.join(base_dir, 'WorkDayTimer.exe')):
                    print_color(f"Executable size: {os.path.getsize(os.path.join(base_dir, 'WorkDayTimer.exe')) / (1024 * 1024):.2f} MB", 'green')
                else:
                    print_color("Executable not found after copy", 'red')
            else:
                print_color("Executable not generated", 'red')
                # List contents of dist directory
                dist_dir = os.path.join(base_dir, 'dist')
                if os.path.exists(dist_dir):
                    print_color(f"Contents of dist directory: {os.listdir(dist_dir)}", 'blue')
                else:
                    print_color("dist directory does not exist", 'red')
        else:
            print_color(f"PyInstaller build failed: {result.stderr}", 'red')
            print_color(f"PyInstaller stdout: {result.stdout}", 'blue')
    except Exception as e:
        print_color(f"PyInstaller build error: {e}", 'red')
        import traceback
        print_color(f"Traceback: {traceback.format_exc()}", 'red')

# Build with cx-Freeze
def build_with_cx_freeze():
    print_color("Building with cx-Freeze...", 'blue')
    setup_file = os.path.join(base_dir, 'build', 'setup_cx.py')
    try:
        result = subprocess.run([sys.executable, setup_file, "build_exe"], 
                              cwd=base_dir, capture_output=True, text=True)
        if result.returncode == 0:
            print_color("cx-Freeze build successful", 'green')
            # Copy executable to root directory
            build_exe_dir = os.path.join(base_dir, 'build', 'exe.win-amd64-3.13')
            if os.path.exists(build_exe_dir):
                cx_exe = os.path.join(build_exe_dir, 'WorkDayTimer_cx.exe')
                if os.path.exists(cx_exe):
                    shutil.copy2(cx_exe, os.path.join(base_dir, 'WorkDayTimer_cx.exe'))
                    print_color("cx-Freeze executable copied to root directory", 'green')
        else:
            print_color(f"cx-Freeze build failed: {result.stderr}", 'red')
    except Exception as e:
        print_color(f"cx-Freeze build error: {e}", 'red')

# Main function
def main():
    print_color("WorkDayTimer Build Script", 'yellow')
    print_color("=" * 50, 'yellow')
    
    # Clean build directories
    clean_build()
    
    # Install dependencies
    install_dependencies()
    
    # Non-interactive mode, default to PyInstaller build
    print_color("Using default build method: PyInstaller", 'blue')
    build_with_pyinstaller()
    
    print_color("=" * 50, 'yellow')
    print_color("Build completed!", 'green')

if __name__ == '__main__':
    main()
