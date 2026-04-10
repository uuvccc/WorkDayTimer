import os
import tempfile
import unittest

from workday_timer.config import get_base_dir, Config


class TestConfig(unittest.TestCase):
    def test_get_base_dir(self):
        """Test that get_base_dir returns a valid directory"""
        base_dir = get_base_dir()
        self.assertTrue(os.path.isdir(base_dir))
    
    def test_config_creation(self):
        """Test that Config object is created correctly"""
        config = Config()
        self.assertIsInstance(config, Config)
        self.assertTrue(hasattr(config, 'base_dir'))
        self.assertTrue(hasattr(config, 'is_flexible'))
    
    def test_config_paths(self):
        """Test that config paths are valid"""
        config = Config()
        self.assertTrue(os.path.isdir(os.path.dirname(config.log_file)))
        self.assertTrue(os.path.isdir(os.path.dirname(config.icon_file)))


if __name__ == '__main__':
    unittest.main()
