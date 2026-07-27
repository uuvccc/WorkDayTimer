import os
from app.config.constants import (
    FLEXIBLE_MODE_FILE,
    REMINDER_SETTINGS_FILE,
    DEFAULT_REMINDER_SETTINGS
)

class ConfigManager:
    def __init__(self):
        self._is_flexible = self._read_flexible_mode()
        self._reminder_settings = self._read_reminder_settings()
    
    def _read_flexible_mode(self) -> bool:
        try:
            with open(FLEXIBLE_MODE_FILE, "r") as f:
                return f.read().strip().lower() == "true"
        except FileNotFoundError:
            return False
    
    def _read_reminder_settings(self) -> dict:
        settings = DEFAULT_REMINDER_SETTINGS.copy()
        try:
            with open(REMINDER_SETTINGS_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().lower() == "true"
                        if key in settings:
                            settings[key] = value
        except FileNotFoundError:
            self._save_reminder_settings(settings)
        return settings
    
    def _save_reminder_settings(self, settings: dict):
        try:
            with open(REMINDER_SETTINGS_FILE, "w") as f:
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Error saving reminder settings: {e}")
    
    @property
    def is_flexible(self) -> bool:
        return self._is_flexible
    
    @is_flexible.setter
    def is_flexible(self, value: bool):
        self._is_flexible = value
        try:
            with open(FLEXIBLE_MODE_FILE, "w") as f:
                f.write(str(value).lower())
        except Exception as e:
            print(f"Error saving flexible mode: {e}")
            raise
    
    @property
    def reminder_settings(self) -> dict:
        return self._reminder_settings.copy()
    
    def get_reminder_setting(self, key: str) -> bool:
        return self._reminder_settings.get(key, True)
    
    def set_reminder_setting(self, key: str, value: bool):
        if key in self._reminder_settings:
            self._reminder_settings[key] = value
            self._save_reminder_settings(self._reminder_settings)
        else:
            raise ValueError(f"Unknown reminder setting: {key}")
    
    def toggle_reminder_setting(self, key: str) -> bool:
        if key in self._reminder_settings:
            self._reminder_settings[key] = not self._reminder_settings[key]
            self._save_reminder_settings(self._reminder_settings)
            return self._reminder_settings[key]
        raise ValueError(f"Unknown reminder setting: {key}")

config_manager = ConfigManager()