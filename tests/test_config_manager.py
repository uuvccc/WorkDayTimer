import unittest
from unittest.mock import patch, mock_open
from app.config.manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def test_default_reminder_settings(self):
        from app.config.constants import REMINDER_SETTINGS_FILE
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

if __name__ == '__main__':
    unittest.main()