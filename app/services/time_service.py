import datetime
import os
from app.config.constants import START_TIME_FILE

class TimeService:
    def get_last_start_time(self):
        """Reads the last start time from the config file. Returns None if not found."""
        try:
            with open(START_TIME_FILE, "r") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    try:
                        return datetime.datetime.strptime(last_line, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        print("Warning: Invalid date format in config file. Using current time.")
                        return None
                else:
                    return None
        except FileNotFoundError:
            return None

    def write_start_time(self, start_time):
        """Writes the start time to the config file."""
        try:
            with open(START_TIME_FILE, "a") as f:
                f.write(start_time.strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")
        except Exception as e:
            print(f"Error writing to config file: {e}")

    def is_first_start_of_day(self):
        """Check if this is the first start of the day."""
        current_time = datetime.datetime.now()
        last_start_time = self.get_last_start_time()
        return last_start_time is None or last_start_time.date() != current_time.date()

    def calculate_work_end_time(self, start_time=None, is_flexible=True):
        """Calculate the work end time based on start time and mode."""
        if start_time is None:
            start_time = datetime.datetime.now()

        adjusted_start_time = start_time - datetime.timedelta(seconds=92)

        if not is_flexible:
            morning_nine = datetime.time(9, 0)
            adjusted_start_time = datetime.datetime.combine(start_time.date(), morning_nine)

        adjusted_start_time = adjusted_start_time.replace(second=0, microsecond=0)
        work_end_time = adjusted_start_time + datetime.timedelta(hours=8.5)
        job_record_time = adjusted_start_time + datetime.timedelta(hours=7.5)

        return adjusted_start_time, work_end_time, job_record_time

    def calculate_remaining_seconds(self, target_time):
        """Calculate remaining seconds until target time."""
        now = datetime.datetime.now()
        delta = target_time - now
        return max(0, delta.total_seconds())

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