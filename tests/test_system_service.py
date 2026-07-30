"""
Tests for SystemService — auto-start, shutdown, QQ window toggle.
All registry operations are mocked; no real system changes occur.
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# In-memory fake winreg module for total control
# ---------------------------------------------------------------------------

class FakeRegKey:
    """Simulates a registry key handle for SetValueEx / DeleteValue / QueryValueEx."""

    def __init__(self, initial_values=None):
        self._values = dict(initial_values or {})
        self.closed = False

    def _set(self, name, value):
        self._values[name] = value

    def _delete(self, name):
        if name not in self._values:
            raise FileNotFoundError(f"Cannot delete '{name}'")
        del self._values[name]

    def _query(self, name):
        if name not in self._values:
            raise FileNotFoundError(f"Value '{name}' not found")
        return (1, self._values[name])

    def _close(self):
        self.closed = True


def _make_fake_winreg(reg_dict):
    """Build a fake winreg module backed by an in-memory registry dict.

    Args:
        reg_dict: dict mapping registry-key-path → FakeRegKey
    Returns:
        MagicMock with OpenKey / SetValueEx / DeleteValue / CloseKey / QueryValueEx
    """
    fake = MagicMock(name='winreg')

    def _open_key(hkey, subkey, reserved, access):
        return reg_dict.get(subkey, FakeRegKey())

    def _set_value_ex(key, value_name, reserved, value_type, value):
        key._set(value_name, value)

    def _delete_value(key, value_name):
        key._delete(value_name)

    def _close_key(key):
        key._close()

    def _query_value_ex(key, value_name):
        return key._query(value_name)

    fake.OpenKey.side_effect = _open_key
    fake.SetValueEx.side_effect = _set_value_ex
    fake.DeleteValue.side_effect = _delete_value
    fake.CloseKey.side_effect = _close_key
    fake.QueryValueEx.side_effect = _query_value_ex
    fake.HKEY_CURRENT_USER = None
    fake.KEY_READ = 131097
    fake.KEY_WRITE = 131078
    fake.REG_SZ = 1

    return fake


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestToggleRunOnStartup(unittest.TestCase):
    """Tests for toggle_run_on_startup (enable / disable)."""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_enable_writes_registry_value(self):
        """开启自启：写入 MiniTools 值到注册表"""
        reg_key = FakeRegKey()
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg), \
             patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Tools\MiniTools.exe'):
            ok, msg = self.svc.toggle_run_on_startup(True)
        self.assertTrue(ok, msg=f"Expected True, got: {msg}")
        self.assertIn("MiniTools", reg_key._values)
        self.assertTrue(reg_key.closed)

    def test_disable_removes_registry_value(self):
        """关闭自启：删除 MiniTools 值"""
        reg_key = FakeRegKey({"MiniTools": r'"C:\Tools\MiniTools.exe"'})
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            ok, msg = self.svc.toggle_run_on_startup(False)
        self.assertTrue(ok)
        self.assertNotIn("MiniTools", reg_key._values)

    def test_disable_also_cleans_old_workdaytimer_key(self):
        """关闭自启：同时删除旧 WorkDayTimer 条目"""
        reg_key = FakeRegKey({
            "MiniTools": r'"C:\Tools\MiniTools.exe"',
            "WorkDayTimer": r'"C:\Old\WorkDayTimer.exe"',
        })
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            ok, msg = self.svc.toggle_run_on_startup(False)
        self.assertTrue(ok)
        self.assertNotIn("MiniTools", reg_key._values)
        self.assertNotIn("WorkDayTimer", reg_key._values)

    def test_enable_cleans_old_workdaytimer_key(self):
        """开启自启：写入时清理旧 WorkDayTimer 条目"""
        reg_key = FakeRegKey({"WorkDayTimer": r'"C:\Old\WorkDayTimer.exe"'})
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg), \
             patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Tools\MiniTools.exe'):
            ok, msg = self.svc.toggle_run_on_startup(True)
        self.assertTrue(ok)
        self.assertIn("MiniTools", reg_key._values)
        self.assertNotIn("WorkDayTimer", reg_key._values)

    def test_disable_when_not_present_is_noop(self):
        """关闭自启时条目不存在：不报错"""
        reg_key = FakeRegKey()
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            ok, msg = self.svc.toggle_run_on_startup(False)
        self.assertTrue(ok)

    def test_registry_error_returns_failure(self):
        """注册表操作异常：返回 False + 错误信息"""
        fake_winreg = MagicMock(name='winreg')
        fake_winreg.OpenKey.side_effect = PermissionError("Access denied")

        with patch.dict('sys.modules', winreg=fake_winreg):
            ok, msg = self.svc.toggle_run_on_startup(True)
        self.assertFalse(ok)
        self.assertIn("Access denied", msg)

    def test_enable_uses_correct_app_name(self):
        """开启自启：注册表键名为 APP_NAME = 'MiniTools'"""
        reg_key = FakeRegKey()
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg), \
             patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Tools\MiniTools.exe'):
            self.svc.toggle_run_on_startup(True)
        self.assertIn("MiniTools", reg_key._values)


class TestIsRunOnStartup(unittest.TestCase):
    """Tests for is_run_on_startup()."""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_returns_true_when_minitools_present(self):
        """MiniTools 在注册表中 → True"""
        reg_key = FakeRegKey({"MiniTools": r'"C:\Tools\MiniTools.exe"'})
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            self.assertTrue(self.svc.is_run_on_startup())

    def test_returns_true_when_old_name_present(self):
        """旧 WorkDayTimer 条目存在 → True（兼容）"""
        reg_key = FakeRegKey({"WorkDayTimer": r'"C:\Old\WorkDayTimer.exe"'})
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            self.assertTrue(self.svc.is_run_on_startup())

    def test_returns_false_when_nothing_present(self):
        """注册表中无条目 → False"""
        reg_key = FakeRegKey()
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg):
            self.assertFalse(self.svc.is_run_on_startup())

    def test_returns_false_on_registry_error(self):
        """OpenKey 失败 → False（静默）"""
        fake_winreg = MagicMock(name='winreg')
        fake_winreg.OpenKey.side_effect = OSError("Registry error")

        with patch.dict('sys.modules', winreg=fake_winreg):
            self.assertFalse(self.svc.is_run_on_startup())


class TestGetStartupCommand(unittest.TestCase):
    """Tests for _get_startup_command() with exe / script detection."""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_frozen_exe_returns_exe_path(self):
        """打包为 exe：返回 exe 路径"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Program Files\MiniTools\MiniTools.exe'):
            cmd = self.svc._get_startup_command()
            self.assertEqual(cmd, '"C:\\Program Files\\MiniTools\\MiniTools.exe"')

    def test_script_mode_uses_pythonw(self):
        """脚本模式：使用 pythonw.exe + 脚本路径"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=False), \
             patch.object(sys, 'executable', r'C:\Python310\python.exe'), \
             patch.object(sys, 'argv', [r'D:\repo\MiniTools\main.py']), \
             patch.object(os.path, 'exists', return_value=True):
            cmd = self.svc._get_startup_command()
        expected_pythonw = os.path.join(os.path.dirname(r'C:\Python310\python.exe'), "pythonw.exe")
        self.assertIn(expected_pythonw, cmd)
        self.assertIn(r'D:\repo\MiniTools\main.py', cmd)

    def test_script_mode_fallback_when_no_pythonw(self):
        """脚本模式 pythonw.exe 不存在时回退到 python.exe"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=False), \
             patch.object(sys, 'executable', r'C:\Python310\python.exe'), \
             patch.object(sys, 'argv', [r'D:\repo\MiniTools\main.py']), \
             patch.object(os.path, 'exists', return_value=False):
            cmd = self.svc._get_startup_command()
        self.assertIn('python.exe', cmd)

    def test_startup_command_has_quotes(self):
        """启动命令中的路径都带引号"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\My Tools\app.exe'):
            cmd = self.svc._get_startup_command()
        self.assertTrue(cmd.startswith('"'))
        self.assertTrue(cmd.endswith('"'))


class TestGetExePath(unittest.TestCase):
    """Tests for get_exe_path()."""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_frozen_returns_sys_executable(self):
        """打包模式：返回 sys.executable"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Tools\MiniTools.exe'):
            self.assertEqual(self.svc.get_exe_path(), r'C:\Tools\MiniTools.exe')

    def test_script_returns_argv_absolute(self):
        """脚本模式：返回脚本绝对路径"""
        with patch.object(self.svc, 'is_running_as_exe', return_value=False), \
             patch.object(sys, 'argv', ['main.py']), \
             patch('os.path.abspath', return_value=r'D:\repo\MiniTools\main.py'):
            self.assertEqual(self.svc.get_exe_path(), r'D:\repo\MiniTools\main.py')


class TestFullEnableDisableCycle(unittest.TestCase):
    """End-to-end: enable → check → disable → check"""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_full_cycle(self):
        """完整流程：未启用 → 启用 → 验证 → 关闭 → 验证"""
        reg_key = FakeRegKey()
        fake_winreg = _make_fake_winreg({RUN_KEY: reg_key})

        with patch.dict('sys.modules', winreg=fake_winreg), \
             patch.object(self.svc, 'is_running_as_exe', return_value=True), \
             patch.object(sys, 'executable', r'C:\Tools\MiniTools.exe'):
            # 初始状态：未启用
            self.assertFalse(self.svc.is_run_on_startup())

            # 启用
            ok, msg = self.svc.toggle_run_on_startup(True)
            self.assertTrue(ok)
            self.assertTrue(self.svc.is_run_on_startup())
            self.assertIn("MiniTools", reg_key._values)

            # 关闭
            ok, msg = self.svc.toggle_run_on_startup(False)
            self.assertTrue(ok)
            self.assertFalse(self.svc.is_run_on_startup())


class TestShutdown(unittest.TestCase):
    """Tests for shutdown_computer()."""

    def setUp(self):
        from app.services.system_service import SystemService
        self.svc = SystemService()

    def test_shutdown_calls_command(self):
        """关机：调用 os.system('shutdown /s /t 1')"""
        with patch('os.system') as mock_os:
            ok, msg = self.svc.shutdown_computer()
        self.assertTrue(ok)
        mock_os.assert_called_once_with("shutdown /s /t 1")

    def test_shutdown_handles_exception(self):
        """关机异常：返回 False"""
        with patch('os.system', side_effect=Exception("boom")):
            ok, msg = self.svc.shutdown_computer()
        self.assertFalse(ok)
        self.assertIn("boom", msg)


if __name__ == '__main__':
    unittest.main()
