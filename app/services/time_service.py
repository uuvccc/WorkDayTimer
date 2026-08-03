import datetime
import os
from app.config.constants import START_TIME_FILE
from app.config.manager import config_manager
from app.utils.logger import logger

class TimeService:
    def get_last_start_time(self):
        """Reads the last start time from the config file. Returns None if not found."""
        try:
            with open(START_TIME_FILE, "r") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    try:
                        result = datetime.datetime.strptime(last_line, "%Y-%m-%d %H:%M:%S.%f")
                        logger.debug(f"Read last start time from file: {result}")
                        return result
                    except ValueError:
                        logger.warning(f"Invalid date format in start time file: '{last_line}'")
                        return None
                else:
                    logger.debug("Start time file is empty")
                    return None
        except FileNotFoundError:
            logger.debug(f"Start time file not found: {START_TIME_FILE}")
            return None

    def write_start_time(self, start_time):
        """Writes the start time to the config file."""
        try:
            with open(START_TIME_FILE, "a") as f:
                f.write(start_time.strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")
            logger.info(f"Start time written: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error writing start time: {e}")

    def is_first_start_of_day(self):
        """Check if this is the first start of the day."""
        current_time = datetime.datetime.now()
        last_start_time = self.get_last_start_time()
        is_first = last_start_time is None or last_start_time.date() != current_time.date()
        logger.debug(f"is_first_start_of_day: {is_first} (last={last_start_time}, now={current_time.date()})")
        return is_first

    def calculate_work_end_time(self, start_time=None, is_flexible=True):
        """Calculate the work end time based on start time and mode."""
        if start_time is None:
            start_time = datetime.datetime.now()

        adjusted_start_time = start_time - datetime.timedelta(seconds=92)
        work_hours = config_manager.work_hours
        fixed_start_hour = config_manager.fixed_start_hour
        before_end_minutes = config_manager.job_record_before_end_minutes

        logger.debug(f"calculate_work_end_time: start={start_time.strftime('%H:%M')}, flexible={is_flexible}, "
                     f"work_hours={work_hours}, fixed_start={fixed_start_hour}, before_end_min={before_end_minutes}")

        if not is_flexible:
            hour = int(fixed_start_hour)
            minute = int((fixed_start_hour - hour) * 60)
            fixed_time = datetime.time(hour, minute)
            adjusted_start_time = datetime.datetime.combine(start_time.date(), fixed_time)
            logger.debug(f"Fixed mode: adjusted_start={adjusted_start_time.strftime('%H:%M')}")

        adjusted_start_time = adjusted_start_time.replace(second=0, microsecond=0)
        work_end_time = adjusted_start_time + datetime.timedelta(hours=work_hours)
        job_record_time = work_end_time - datetime.timedelta(minutes=before_end_minutes)

        logger.info(f"Work time calculated: adjusted_start={adjusted_start_time.strftime('%H:%M')}, "
                    f"work_end={work_end_time.strftime('%H:%M')}, job_record={job_record_time.strftime('%H:%M')}")
        return adjusted_start_time, work_end_time, job_record_time

    def calculate_remaining_seconds(self, target_time):
        """Calculate remaining seconds until target time."""
        now = datetime.datetime.now()
        delta = target_time - now
        seconds = max(0, delta.total_seconds())
        logger.debug(f"Remaining seconds to {target_time.strftime('%H:%M')}: {seconds:.0f}s ({seconds/60:.1f}min)")
        return seconds

    def get_work_progress(self, start_time=None, is_flexible=True):
        """Get work progress as percentage (0-100)."""
        if start_time is None:
            start_time = datetime.datetime.now()

        adjusted_start_time, work_end_time, _ = self.calculate_work_end_time(start_time, is_flexible)
        now = datetime.datetime.now()

        if now < adjusted_start_time:
            return 0.0
        if now >= work_end_time:
            return 100.0

        total_work_seconds = (work_end_time - adjusted_start_time).total_seconds()
        elapsed_seconds = (now - adjusted_start_time).total_seconds()
        return min(100.0, (elapsed_seconds / total_work_seconds) * 100)

time_service = TimeService()