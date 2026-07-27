import unittest
import datetime
from unittest.mock import patch, mock_open
from app.services.time_service import time_service

class TestTimeService(unittest.TestCase):
    def test_calculate_work_end_time_flexible(self):
        start_time = datetime.datetime(2026, 7, 27, 9, 0, 0)
        adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=True)
        
        expected_adjusted = start_time - datetime.timedelta(seconds=92)
        expected_adjusted = expected_adjusted.replace(second=0, microsecond=0)
        expected_end = expected_adjusted + datetime.timedelta(hours=8.5)
        expected_record = expected_adjusted + datetime.timedelta(hours=7.5)
        
        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_calculate_work_end_time_not_flexible(self):
        start_time = datetime.datetime(2026, 7, 27, 10, 30, 0)
        adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=False)
        
        expected_adjusted = datetime.datetime(2026, 7, 27, 9, 0, 0)
        expected_end = expected_adjusted + datetime.timedelta(hours=8.5)
        expected_record = expected_adjusted + datetime.timedelta(hours=7.5)
        
        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_calculate_remaining_seconds_future(self):
        future_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        remaining = time_service.calculate_remaining_seconds(future_time)
        
        self.assertGreater(remaining, 0)
        self.assertLess(remaining, 3601)

    def test_calculate_remaining_seconds_past(self):
        past_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        remaining = time_service.calculate_remaining_seconds(past_time)
        
        self.assertEqual(remaining, 0)

    def test_get_work_progress(self):
        start_time = datetime.datetime.now() - datetime.timedelta(hours=4)
        progress = time_service.get_work_progress(start_time, is_flexible=True)
        
        self.assertGreaterEqual(progress, 0)
        self.assertLessEqual(progress, 100)

    def test_is_first_start_of_day_no_file(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = time_service.is_first_start_of_day()
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()