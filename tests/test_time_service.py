import sys
import unittest
import datetime
from unittest.mock import patch, MagicMock
from app.services.time_service import time_service


class TestTimeService(unittest.TestCase):
    _default_config = {"work_hours": 8.5, "fixed_start_hour": 9.0, "job_record_before_end_minutes": 60}

    def _patch_config(self, **overrides):
        """mock 模块级 config_manager 的三个属性。

        由于 app/services/__init__.py 将 time_service 实例导入到包命名空间，
        app.services.time_service 被实例遮蔽（shadow），无法作为模块路径直接使用，
        因此改用 sys.modules 获取真实模块对象后再 patch。
        """
        values = {**self._default_config, **overrides}
        ts_module = sys.modules["app.services.time_service"]
        mock_config = MagicMock()
        mock_config.work_hours = values["work_hours"]
        mock_config.fixed_start_hour = values["fixed_start_hour"]
        mock_config.job_record_before_end_minutes = values["job_record_before_end_minutes"]
        return patch.object(ts_module, "config_manager", mock_config)

    def test_calculate_work_end_time_flexible(self):
        start_time = datetime.datetime(2026, 7, 27, 9, 0, 0)
        with self._patch_config():
            adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=True)

        expected_adjusted = start_time - datetime.timedelta(seconds=92)
        expected_adjusted = expected_adjusted.replace(second=0, microsecond=0)
        expected_end = expected_adjusted + datetime.timedelta(hours=8.5)
        expected_record = expected_end - datetime.timedelta(minutes=60)

        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_calculate_work_end_time_not_flexible(self):
        start_time = datetime.datetime(2026, 7, 27, 10, 30, 0)
        with self._patch_config():
            adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=False)

        expected_adjusted = datetime.datetime(2026, 7, 27, 9, 0, 0)
        expected_end = expected_adjusted + datetime.timedelta(hours=8.5)
        expected_record = expected_end - datetime.timedelta(minutes=60)

        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_custom_work_hours(self):
        """Custom work_hours = 6.0 → work_end = adjusted_start + 6h."""
        start_time = datetime.datetime(2026, 7, 27, 9, 0, 0)
        with self._patch_config(work_hours=6.0):
            adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=True)

        expected_adjusted = start_time - datetime.timedelta(seconds=92)
        expected_adjusted = expected_adjusted.replace(second=0, microsecond=0)
        expected_end = expected_adjusted + datetime.timedelta(hours=6.0)
        expected_record = expected_end - datetime.timedelta(minutes=60)

        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_custom_fixed_start_hour(self):
        """Custom fixed_start_hour = 10.0 → adjusted_start = 10:00."""
        start_time = datetime.datetime(2026, 7, 27, 15, 0, 0)
        with self._patch_config(fixed_start_hour=10.0, work_hours=8.0):
            adjusted_start, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=False)

        expected_adjusted = datetime.datetime(2026, 7, 27, 10, 0, 0)
        expected_end = expected_adjusted + datetime.timedelta(hours=8.0)
        expected_record = expected_end - datetime.timedelta(minutes=60)

        self.assertEqual(adjusted_start, expected_adjusted)
        self.assertEqual(work_end, expected_end)
        self.assertEqual(job_record, expected_record)

    def test_custom_job_record_before_end(self):
        """Custom job_record_before_end_minutes = 30."""
        start_time = datetime.datetime(2026, 7, 27, 9, 0, 0)
        with self._patch_config(job_record_before_end_minutes=30):
            _, work_end, job_record = time_service.calculate_work_end_time(start_time, is_flexible=True)

        self.assertEqual(job_record, work_end - datetime.timedelta(minutes=30))

    def test_fixed_start_half_hour(self):
        """fixed_start_hour = 8.5 → start at 08:30."""
        start_time = datetime.datetime(2026, 7, 27, 12, 0, 0)
        with self._patch_config(fixed_start_hour=8.5, work_hours=9.0):
            adjusted_start, work_end, _ = time_service.calculate_work_end_time(start_time, is_flexible=False)

        self.assertEqual(adjusted_start, datetime.datetime(2026, 7, 27, 8, 30, 0))
        self.assertEqual(work_end, datetime.datetime(2026, 7, 27, 17, 30, 0))

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
        with self._patch_config():
            progress = time_service.get_work_progress(start_time, is_flexible=True)

        self.assertGreaterEqual(progress, 0)
        self.assertLessEqual(progress, 100)

    def test_is_first_start_of_day_no_file(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = time_service.is_first_start_of_day()
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
