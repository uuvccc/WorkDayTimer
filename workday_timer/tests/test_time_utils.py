import os
import tempfile
import unittest
import datetime

from workday_timer.utils.time_utils import get_last_start_time, write_start_time
from workday_timer.config import config


class TestTimeUtils(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()  # Close the file handle immediately
        self.original_start_time_file = config.start_time_file
        config.start_time_file = self.temp_file.name
    
    def tearDown(self):
        """Clean up test environment"""
        # Restore original file path
        config.start_time_file = self.original_start_time_file
        # Delete temporary file
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_write_start_time(self):
        """Test that start time is written correctly"""
        test_time = datetime.datetime.now()
        write_start_time(test_time)
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(config.start_time_file))
        with open(config.start_time_file, 'r') as f:
            content = f.read()
            self.assertIn(test_time.strftime("%Y-%m-%d %H:%M:%S.%f"), content)
    
    def test_get_last_start_time(self):
        """Test that last start time is retrieved correctly"""
        # Write a test time
        test_time = datetime.datetime.now()
        write_start_time(test_time)
        
        # Get last start time
        last_time = get_last_start_time()
        self.assertIsInstance(last_time, datetime.datetime)
        self.assertEqual(last_time.strftime("%Y-%m-%d %H:%M:%S.%f"), test_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
    
    def test_get_last_start_time_no_file(self):
        """Test that get_last_start_time returns None when file doesn't exist"""
        # Ensure file doesn't exist
        if os.path.exists(config.start_time_file):
            os.unlink(config.start_time_file)
        
        last_time = get_last_start_time()
        self.assertIsNone(last_time)


if __name__ == '__main__':
    unittest.main()
