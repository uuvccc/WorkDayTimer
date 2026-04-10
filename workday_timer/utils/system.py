import os
import win32gui
import win32con


def toggle_qq_window():
    """Toggle visibility of windows with 'QQ..exe' in the title"""
    def window_enum_callback(hwnd, extra):
        if "QQ..exe" in win32gui.GetWindowText(hwnd):
            # Check if window is visible
            if win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    
    win32gui.EnumWindows(window_enum_callback, None)


def shutdown_computer():
    """Shutdown the computer"""
    # **WARNING:  Use with EXTREME caution!**  Add robust confirmation dialog before implementing.
    try:
        os.system("shutdown /s /t 1") #Windows shutdown command, adjust for other OS.
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", f"Shutdown failed: {e}")


def is_run_on_startup():
    """Check if the application is set to run on startup"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, "WorkDayTimer")
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def toggle_run_on_startup():
    """Toggle run on startup setting"""
    import sys
    from PyQt5.QtWidgets import QMessageBox
    
    is_enabled = not is_run_on_startup()
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        try:
            if is_enabled:
                # Add to startup
                exe_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "WorkDayTimer", 0, winreg.REG_SZ, f'"{exe_path}"')
                QMessageBox.information(None, "Startup Setting", "Application has been added to startup.")
            else:
                # Remove from startup
                winreg.DeleteValue(key, "WorkDayTimer")
                QMessageBox.information(None, "Startup Setting", "Application has been removed from startup.")
        except FileNotFoundError:
            if not is_enabled:
                # Already not in startup
                QMessageBox.information(None, "Startup Setting", "Application is not in startup.")
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to update startup setting: {e}")
