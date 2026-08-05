import json
import os
import datetime
from app.config.constants import (
    SETTINGS_FILE,
    OLD_FLEXIBLE_MODE_FILE,
    OLD_REMINDER_SETTINGS_FILE,
    DEFAULT_SETTINGS,
    DEFER_UPDATE_DAYS,
)
from app.utils.logger import logger


class ConfigManager:
    def __init__(self):
        self._settings = DEFAULT_SETTINGS.copy()
        logger.debug("ConfigManager initializing...")
        self._migrate_old_files()
        self._load()
        logger.info(f"ConfigManager loaded: flexible={self.is_flexible}, "
                    f"startup={self.run_on_startup}, work_hours={self.work_hours}, "
                    f"auto_check_update={self.auto_check_update}, "
                    f"check_update_delay={self.check_update_delay}, "
                    f"reminders={self.reminder_settings}")

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
            logger.debug(f"Settings loaded from {SETTINGS_FILE}")
        except FileNotFoundError:
            logger.info(f"Settings file not found, creating default: {SETTINGS_FILE}")
            self._save()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}", exc_info=True)

    def _save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.debug(f"Settings saved to {SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}", exc_info=True)

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
        old = self._settings.get("flexible_mode", False)
        self._settings["flexible_mode"] = value
        self._save()
        logger.info(f"flexible_mode changed: {old} -> {value}")

    # ── Run on Startup ────────────────────────────────────

    @property
    def run_on_startup(self) -> bool:
        return self._settings.get("run_on_startup", False)

    @run_on_startup.setter
    def run_on_startup(self, value: bool):
        old = self._settings.get("run_on_startup", False)
        self._settings["run_on_startup"] = value
        self._save()
        logger.info(f"run_on_startup changed: {old} -> {value}")

    # ── Auto Check Update ────────────────────────────────

    @property
    def auto_check_update(self) -> bool:
        return self._settings.get("auto_check_update", True)

    @auto_check_update.setter
    def auto_check_update(self, value: bool):
        old = self._settings.get("auto_check_update", True)
        self._settings["auto_check_update"] = value
        self._save()
        logger.info(f"auto_check_update changed: {old} -> {value}")

    @property
    def check_update_delay(self) -> int:
        return self._settings.get("check_update_delay", 10)

    @check_update_delay.setter
    def check_update_delay(self, value: int):
        old = self._settings.get("check_update_delay", 10)
        self._settings["check_update_delay"] = value
        self._save()
        logger.info(f"check_update_delay changed: {old} -> {value}")

    def should_auto_check(self) -> bool:
        """是否应该执行自动检测：开关打开 且 defer 已过期/不存在"""
        if not self.auto_check_update:
            return False
        defer_until = self._settings.get("defer_update_until")
        if defer_until is None:
            return True
        try:
            defer_dt = datetime.datetime.fromisoformat(defer_until)
            if datetime.datetime.now() < defer_dt:
                logger.info(f"Update check deferred until {defer_until}, skipping")
                return False
            # defer 已过期，清除
            self._settings["defer_update_until"] = None
            self._save()
            return True
        except (ValueError, TypeError):
            return True

    def defer_update(self):
        """用户选择“下次提醒”，7 天内不再自动检测"""
        until = (datetime.datetime.now()
                 + datetime.timedelta(days=DEFER_UPDATE_DAYS)).isoformat()
        self._settings["defer_update_until"] = until
        self._save()
        logger.info(f"Update check deferred until {until}")

    def clear_defer(self):
        """清除 defer 记录（完成更新后调用）"""
        self._settings.pop("defer_update_until", None)
        self._save()
        logger.debug("Update defer cleared")

    # ── Work Hours ────────────────────────────────────────

    @property
    def work_hours(self) -> float:
        return self._settings.get("work_hours", 8.5)

    @work_hours.setter
    def work_hours(self, value: float):
        old = self._settings.get("work_hours", 8.5)
        self._settings["work_hours"] = value
        self._save()
        logger.info(f"work_hours changed: {old} -> {value}")

    @property
    def fixed_start_hour(self) -> float:
        return self._settings.get("fixed_start_hour", 9.0)

    @fixed_start_hour.setter
    def fixed_start_hour(self, value: float):
        old = self._settings.get("fixed_start_hour", 9.0)
        self._settings["fixed_start_hour"] = value
        self._save()
        logger.info(f"fixed_start_hour changed: {old} -> {value}")

    @property
    def job_record_before_end_minutes(self) -> int:
        return self._settings.get("job_record_before_end_minutes", 60)

    @job_record_before_end_minutes.setter
    def job_record_before_end_minutes(self, value: int):
        old = self._settings.get("job_record_before_end_minutes", 60)
        self._settings["job_record_before_end_minutes"] = value
        self._save()
        logger.info(f"job_record_before_end_minutes changed: {old} -> {value}")

    # ── Reminder Settings ─────────────────────────────────

    @property
    def reminder_settings(self) -> dict:
        return self._settings.get("reminders", {}).copy()

    def get_reminder_setting(self, key: str) -> bool:
        return self._settings.get("reminders", {}).get(key, True)

    def set_reminder_setting(self, key: str, value: bool):
        if key not in self._settings.get("reminders", {}):
            raise ValueError(f"Unknown reminder setting: {key}")
        old = self._settings["reminders"].get(key, True)
        self._settings["reminders"][key] = value
        self._save()
        logger.info(f"reminder '{key}' changed: {old} -> {value}")

    def toggle_reminder_setting(self, key: str) -> bool:
        current = self.get_reminder_setting(key)
        self.set_reminder_setting(key, not current)
        return not current

    # ── Bulk ──────────────────────────────────────────────

    def get_all(self) -> dict:
        return {
            "flexible_mode": self.is_flexible,
            "run_on_startup": self.run_on_startup,
            "auto_check_update": self.auto_check_update,
            "check_update_delay": self.check_update_delay,
            "work_hours": self.work_hours,
            "fixed_start_hour": self.fixed_start_hour,
            "job_record_before_end_minutes": self.job_record_before_end_minutes,
            "reminders": self.reminder_settings,
        }

    def apply_changes(self, flexible_mode=None, run_on_startup=None,
                      auto_check_update=None, check_update_delay=None,
                      work_hours=None, fixed_start_hour=None,
                      job_record_before_end_minutes=None, reminders=None):
        """批量写入（避免多次 save）"""
        changes = []
        if flexible_mode is not None:
            changes.append(f"flexible_mode: {self._settings.get('flexible_mode')} -> {flexible_mode}")
            self._settings["flexible_mode"] = flexible_mode
        if run_on_startup is not None:
            changes.append(f"run_on_startup: {self._settings.get('run_on_startup')} -> {run_on_startup}")
            self._settings["run_on_startup"] = run_on_startup
        if auto_check_update is not None:
            changes.append(f"auto_check_update: {self._settings.get('auto_check_update')} -> {auto_check_update}")
            self._settings["auto_check_update"] = auto_check_update
        if check_update_delay is not None:
            changes.append(f"check_update_delay: {self._settings.get('check_update_delay')} -> {check_update_delay}")
            self._settings["check_update_delay"] = check_update_delay
        if work_hours is not None:
            changes.append(f"work_hours: {self._settings.get('work_hours')} -> {work_hours}")
            self._settings["work_hours"] = work_hours
        if fixed_start_hour is not None:
            changes.append(f"fixed_start_hour: {self._settings.get('fixed_start_hour')} -> {fixed_start_hour}")
            self._settings["fixed_start_hour"] = fixed_start_hour
        if job_record_before_end_minutes is not None:
            changes.append(f"job_record_before_end_minutes: {self._settings.get('job_record_before_end_minutes')} -> {job_record_before_end_minutes}")
            self._settings["job_record_before_end_minutes"] = job_record_before_end_minutes
        if reminders is not None:
            changes.append(f"reminders: {self._settings.get('reminders')} -> {reminders}")
            self._settings["reminders"] = reminders
        self._save()
        if changes:
            logger.info(f"Settings batch update: {'; '.join(changes)}")


config_manager = ConfigManager()
