import os
import sys
from app.config.constants import BASE_DIR, get_exe_path, is_packaged
from app.utils.logger import logger


class SystemService:
    APP_NAME = "MiniTools"
    # 新旧两种可能的启动项名称
    STARTUP_NAMES = ("MiniTools", "WorkDayTimer")

    def _read_startup_entry(self):
        """读取启动项，返回 (值名, 命令)；未设置时返回 (None, None)"""
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        try:
            for name in self.STARTUP_NAMES:
                try:
                    command, _ = winreg.QueryValueEx(key, name)
                    return name, command
                except FileNotFoundError:
                    continue
            return None, None
        finally:
            winreg.CloseKey(key)

    def is_run_on_startup(self):
        """Check if the application is set to run on startup"""
        try:
            name, _ = self._read_startup_entry()
            if name:
                logger.debug(f"Startup registry entry found: {name}")
                return True
            logger.debug("No startup registry entry found")
            return False
        except Exception as e:
            logger.warning(f"Failed to read startup registry: {e}")
            return False

    def sync_run_on_startup(self):
        """已开启自启时，把注册表命令校正为当前 exe 路径。

        exe 移动目录或旧版本写入了错误路径（如 Nuitka 打包后的 python.exe）
        时，自启会静默失效，这里在启动时自愈。"""
        try:
            name, command = self._read_startup_entry()
            if not name:
                return
            expected = self._get_startup_command()
            if command and command.strip().lower() == expected.lower() and name == self.APP_NAME:
                return
            ok, msg = self.toggle_run_on_startup(True)
            if ok:
                logger.info(f"Repaired startup command: {command} -> {expected}")
            else:
                logger.warning(f"Failed to repair startup command: {msg}")
        except Exception as e:
            logger.warning(f"Failed to sync startup entry: {e}")

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
                    for name in self.STARTUP_NAMES:
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

            toggled_count = 0

            def window_enum_callback(hwnd, extra):
                nonlocal toggled_count
                if "QQ..exe" in win32gui.GetWindowText(hwnd):
                    if win32gui.IsWindowVisible(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                        logger.debug(f"Hid QQ window: hwnd={hwnd}")
                    else:
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        logger.debug(f"Showed QQ window: hwnd={hwnd}")
                    toggled_count += 1

            win32gui.EnumWindows(window_enum_callback, None)
            logger.info(f"Toggle QQ window completed, toggled {toggled_count} window(s)")
        except ImportError:
            logger.warning("win32gui module not available. Cannot toggle QQ window.")

    def shutdown_computer(self):
        """Shutdown the computer"""
        try:
            logger.warning("Executing system shutdown: shutdown /s /t 1")
            os.system("shutdown /s /t 1")
            return True, "Shutdown initiated."
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            return False, f"Shutdown failed: {e}"

    def _get_startup_command(self):
        """生成写入注册表 Run 键的启动命令行。

        打包模式写 exe 完整路径；源码运行写 pythonw + main.py
        （直接写 sys.executable 会变成裸 python.exe，登录时自启无效）。"""
        if is_packaged():
            return f'"{get_exe_path()}"'
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        main_py = os.path.join(BASE_DIR, "main.py")
        if os.path.isfile(pythonw) and os.path.isfile(main_py):
            return f'"{pythonw}" "{main_py}"'
        return f'"{sys.executable}"'


system_service = SystemService()
