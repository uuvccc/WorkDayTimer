import json
import os
from app.config.constants import (
    SETTINGS_FILE,
    OLD_FLEXIBLE_MODE_FILE,
    OLD_REMINDER_SETTINGS_FILE,
    DEFAULT_SETTINGS,
)
from app.utils.logger import logger


class ConfigManager:
    def __init__(self):
        self._settings = DEFAULT_SETTINGS.copy()
        self._migrate_old_files()
        self._load()

    # ── 文件读写 ──────────────────────────────────────────

    def _load(self):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并：保留旧 key 缺失时用默认值
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            # reminders 子字典也要合并
            if "reminders" in data and isinstance(data["reminders"], dict):
                merged["reminders"] = {**DEFAULT_SETTINGS["reminders"], **data["reminders"]}
            self._settings = merged
        except FileNotFoundError:
            self._save()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def _save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _migrate_old_files(self):
        """将旧的 flexible_mode.txt / reminder_settings.txt 迁移到 settings.json"""
        if os.path.exists(SETTINGS_FILE):
            return  # 已有新配置，不覆盖

        migrated = False
        if os.path.exists(OLD_FLEXIBLE_MODE_FILE):
            try:
                with open(OLD_FLEXIBLE_MODE_FILE, "r") as f:
                    self._settings["flexible_mode"] = f.read().strip().lower() == "true"
                migrated = True
            except Exception:
                pass

        if os.path.exists(OLD_REMINDER_SETTINGS_FILE):
            try:
                with open(OLD_REMINDER_SETTINGS_FILE, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().lower() == "true"
                            if key in self._settings["reminders"]:
                                self._settings["reminders"][key] = val
                migrated = True
            except Exception:
                pass

        if migrated:
            self._save()
            logger.info("Migrated old config files to settings.json")
            # 删除旧文件
            for old_file in (OLD_FLEXIBLE_MODE_FILE, OLD_REMINDER_SETTINGS_FILE):
                try:
                    os.remove(old_file)
                except Exception:
                    pass

    # ── Flexible Mode ─────────────────────────────────────

    @property
    def is_flexible(self) -> bool:
        return self._settings.get("flexible_mode", False)

    @is_flexible.setter
    def is_flexible(self, value: bool):
        self._settings["flexible_mode"] = value
        self._save()

    # ── Run on Startup ────────────────────────────────────

    @property
    def run_on_startup(self) -> bool:
        return self._settings.get("run_on_startup", False)

    @run_on_startup.setter
    def run_on_startup(self, value: bool):
        self._settings["run_on_startup"] = value
        self._save()

    # ── Work Hours ────────────────────────────────────────

    @property
    def work_hours(self) -> float:
        return self._settings.get("work_hours", 8.5)

    @work_hours.setter
    def work_hours(self, value: float):
        self._settings["work_hours"] = value
        self._save()

    @property
    def fixed_start_hour(self) -> float:
        return self._settings.get("fixed_start_hour", 9.0)

    @fixed_start_hour.setter
    def fixed_start_hour(self, value: float):
        self._settings["fixed_start_hour"] = value
        self._save()

    @property
    def job_record_before_end_minutes(self) -> int:
        return self._settings.get("job_record_before_end_minutes", 60)

    @job_record_before_end_minutes.setter
    def job_record_before_end_minutes(self, value: int):
        self._settings["job_record_before_end_minutes"] = value
        self._save()

    # ── Reminder Settings ─────────────────────────────────

    @property
    def reminder_settings(self) -> dict:
        return self._settings.get("reminders", {}).copy()

    def get_reminder_setting(self, key: str) -> bool:
        return self._settings.get("reminders", {}).get(key, True)

    def set_reminder_setting(self, key: str, value: bool):
        if key not in self._settings.get("reminders", {}):
            raise ValueError(f"Unknown reminder setting: {key}")
        self._settings["reminders"][key] = value
        self._save()

    def toggle_reminder_setting(self, key: str) -> bool:
        current = self.get_reminder_setting(key)
        self.set_reminder_setting(key, not current)
        return not current

    # ── Bulk ──────────────────────────────────────────────

    def get_all(self) -> dict:
        return {
            "flexible_mode": self.is_flexible,
            "run_on_startup": self.run_on_startup,
            "work_hours": self.work_hours,
            "fixed_start_hour": self.fixed_start_hour,
            "job_record_before_end_minutes": self.job_record_before_end_minutes,
            "reminders": self.reminder_settings,
        }

    def apply_changes(self, flexible_mode=None, run_on_startup=None,
                      work_hours=None, fixed_start_hour=None,
                      job_record_before_end_minutes=None, reminders=None):
        """批量写入（避免多次 save）"""
        if flexible_mode is not None:
            self._settings["flexible_mode"] = flexible_mode
        if run_on_startup is not None:
            self._settings["run_on_startup"] = run_on_startup
        if work_hours is not None:
            self._settings["work_hours"] = work_hours
        if fixed_start_hour is not None:
            self._settings["fixed_start_hour"] = fixed_start_hour
        if job_record_before_end_minutes is not None:
            self._settings["job_record_before_end_minutes"] = job_record_before_end_minutes
        if reminders is not None:
            self._settings["reminders"] = reminders
        self._save()


config_manager = ConfigManager()
