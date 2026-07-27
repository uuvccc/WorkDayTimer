import os
import sys

class SystemService:
    APP_NAME = "MiniTools"

    def is_run_on_startup(self):
        """Check if the application is set to run on startup"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
            except FileNotFoundError:
                try:
                    winreg.QueryValueEx(key, "WorkDayTimer")
                    return True
                except FileNotFoundError:
                    return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def toggle_run_on_startup(self, is_enabled):
        """Toggle run on startup setting"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            try:
                if is_enabled:
                    exe_path = os.path.abspath(sys.argv[0])
                    winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                    try:
                        winreg.DeleteValue(key, "WorkDayTimer")
                    except FileNotFoundError:
                        pass
                    return True, "Application has been added to startup."
                else:
                    try:
                        winreg.DeleteValue(key, self.APP_NAME)
                    except FileNotFoundError:
                        pass
                    try:
                        winreg.DeleteValue(key, "WorkDayTimer")
                    except FileNotFoundError:
                        pass
                    return True, "Application has been removed from startup."
            except FileNotFoundError:
                if not is_enabled:
                    return True, "Application is not in startup."
                return False, "Failed to add application to startup."
            finally:
                winreg.CloseKey(key)
        except Exception as e:
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
        """Get the path to the current executable"""
        return os.path.abspath(sys.argv[0])

    def is_running_as_exe(self):
        """Check if running as executable"""
        return getattr(sys, 'frozen', False)

system_service = SystemService()