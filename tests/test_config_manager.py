import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

from app.config import manager as config_manager_module
from app.config.manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """注意：set_reminder_setting / toggle / setter 会 _save() 写盘。
    必须把 SETTINGS_FILE 重定向到临时文件，避免测试把用户的 settings.json 写坏。"""

    @classmethod
    def setUpClass(cls):
        # 记录真实路径，测试期间改指向临时文件
        cls._orig_settings_file = config_manager_module.SETTINGS_FILE
        cls._tmp_settings_file = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        )
        cls._tmp_settings_file.close()
        config_manager_module.SETTINGS_FILE = cls._tmp_settings_file.name

    @classmethod
    def tearDownClass(cls):
        config_manager_module.SETTINGS_FILE = cls._orig_settings_file
        try:
            os.remove(cls._tmp_settings_file.name)
        except FileNotFoundError:
            pass

    def test_default_reminder_settings(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            self.assertTrue(config.get_reminder_setting('checkin_reminder'))
            self.assertTrue(config.get_reminder_setting('job_record_reminder'))
            self.assertTrue(config.get_reminder_setting('checkout_reminder'))

    def test_set_reminder_setting(self):
        config = ConfigManager()
        original_value = config.get_reminder_setting('checkin_reminder')
        
        config.set_reminder_setting('checkin_reminder', not original_value)
        self.assertEqual(config.get_reminder_setting('checkin_reminder'), not original_value)

    def test_toggle_reminder_setting(self):
        config = ConfigManager()
        original_value = config.get_reminder_setting('job_record_reminder')
        
        new_value = config.toggle_reminder_setting('job_record_reminder')
        self.assertEqual(new_value, not original_value)
        
        new_value = config.toggle_reminder_setting('job_record_reminder')
        self.assertEqual(new_value, original_value)

    def test_get_reminder_setting_invalid_key(self):
        config = ConfigManager()
        
        with self.assertRaises(ValueError):
            config.set_reminder_setting('invalid_key', True)

    def test_toggle_reminder_setting_invalid_key(self):
        config = ConfigManager()
        
        with self.assertRaises(ValueError):
            config.toggle_reminder_setting('invalid_key')

    def test_flexible_mode_default(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            self.assertFalse(config.is_flexible)

    def test_work_hours_default(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            self.assertEqual(config.work_hours, 8.5)

    def test_work_hours_set_get(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            config.work_hours = 7.0
            self.assertEqual(config.work_hours, 7.0)

    def test_fixed_start_hour_default(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            self.assertEqual(config.fixed_start_hour, 9.0)

    def test_job_record_before_end_minutes_default(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = ConfigManager()
            self.assertEqual(config.job_record_before_end_minutes, 60)


if __name__ == '__main__':
    unittest.main()