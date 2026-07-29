import os
import sys
from app.utils.logger import logger


class SystemService:
    APP_NAME = "MiniTools"

    def is_run_on_startup(self):
        """Check if the application is set to run on startup"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            try:
                # 检查新旧两种可能的启动项名称
                for name in (self.APP_NAME, "WorkDayTimer"):
                    try:
                        winreg.QueryValueEx(key, name)
                        return True
                    except FileNotFoundError:
                        continue
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def toggle_run_on_startup(self, is_enabled):
        """Toggle run on startup setting"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE | winreg.KEY_READ,
            )
            try:
                if is_enabled:
                    startup_cmd = self._get_startup_command()
                    winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, startup_cmd)
                    # 清理旧的启动项名称
                    try:
                        winreg.DeleteValue(key, "WorkDayTimer")
                    except FileNotFoundError:
                        pass
                    logger.info(f"Added to startup: {startup_cmd}")
                    return True, "Application has been added to startup."
                else:
                    for name in (self.APP_NAME, "WorkDayTimer"):
                        try:
                            winreg.DeleteValue(key, name)
                            logger.info(f"Removed from startup: {name}")
                        except FileNotFoundError:
                            pass
                    return True, "Application has been removed from startup."
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Failed to modify startup settings: {e}", exc_info=True)
            return False, f"Failed to update startup setting: {e}"

    def toggle_qq_window(self):
        """Toggle visibility of windows with 'QQ..exe' in the title"""
        try:
            import win32gui
            import win32con

            def window_enum_callback(hwnd, extra):
                if "QQ..exe" in win32gui.GetWindowText(hwnd):
                    if win32gui.IsWindowVisible(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    else:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

            win32gui.EnumWindows(window_enum_callback, None)
        except ImportError:
            print("Warning: win32gui module not available. Cannot toggle QQ window.")

    def shutdown_computer(self):
        """Shutdown the computer"""
        try:
            os.system("shutdown /s /t 1")
            return True, "Shutdown initiated."
        except Exception as e:
            return False, f"Shutdown failed: {e}"

    def get_exe_path(self):
        """Get the path to the current executable or script"""
        if self.is_running_as_exe():
            return sys.executable
        return os.path.abspath(sys.argv[0])

    def is_running_as_exe(self):
        """Check if running as PyInstaller-frozen executable"""
        return getattr(sys, 'frozen', False)

    def _get_startup_command(self):
        """生成写入注册表 Run 键的启动命令行

        - exe 模式：直接返回 exe 完整路径（带引号）
        - 脚本模式：用 pythonw.exe（无控制台窗口）启动脚本
        """
        if self.is_running_as_exe():
            # PyInstaller 打包的 exe：用 sys.executable 获取真实路径
            return f'"{sys.executable}"'
        else:
            # Python 脚本模式：用 pythonw.exe 避免弹出控制台
            python_dir = os.path.dirname(sys.executable)
            pythonw_path = os.path.join(python_dir, "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable  # 回退到 python.exe
            script_path = os.path.abspath(sys.argv[0])
            return f'"{pythonw_path}" "{script_path}"'


system_service = SystemService()
