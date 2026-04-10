import datetime
import os

from workday_timer.config import config


def get_last_start_time():
    """Reads the last start time from the config file. Returns None if not found."""
    try:
        with open(config.start_time_file, "r") as f:
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


def write_start_time(start_time):
    """Writes the start time to the config file."""
    try:
        with open(config.start_time_file, "a") as f:
            f.write(start_time.strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")
    except Exception as e:
        print(f"Error writing to config file: {e}")
