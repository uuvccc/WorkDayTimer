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
            "reminders": self.reminder_settings,
        }

    def apply_changes(self, flexible_mode=None, run_on_startup=None, reminders=None):
        """批量写入（避免多次 save）"""
        if flexible_mode is not None:
            self._settings["flexible_mode"] = flexible_mode
        if run_on_startup is not None:
            self._settings["run_on_startup"] = run_on_startup
        if reminders is not None:
            self._settings["reminders"] = reminders
        self._save()


config_manager = ConfigManager()
