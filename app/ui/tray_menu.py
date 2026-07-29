from PyQt5.QtWidgets import QMenu, QAction, QSystemTrayIcon, QStyle
from PyQt5.QtGui import QIcon
import os
from app.config.manager import config_manager
from app.services import system_service


class TrayMenu:
    def __init__(self, icon_file, parent=None):
        self.parent = parent
        self.tray_icon = QSystemTrayIcon(parent)
        self._setup_icon(icon_file)
        self.menu = QMenu(parent)
        self._setup_menu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        self._sync_state()

    def _setup_icon(self, icon_file):
        if os.path.exists(icon_file):
            self.tray_icon.setIcon(QIcon(icon_file))
        else:
            self.tray_icon.setIcon(QStyle.SP_MessageBoxInformation)

    def _setup_menu(self):
        self.open_action = QAction("Open", self.parent)
        self.flexible_action = QAction("Flexible Mode", self.parent)
        self.flexible_action.setCheckable(True)
        self.custom_timer_action = QAction("Custom Timer", self.parent)
        self.settings_action = QAction("Settings", self.parent)
        self.update_action = QAction("Update Application", self.parent)
        self.startup_action = QAction("Run on Startup", self.parent)
        self.startup_action.setCheckable(True)
        self.exit_action = QAction("Exit", self.parent)

        self.menu.addAction(self.open_action)
        self.menu.addAction(self.flexible_action)
        self.menu.addAction(self.custom_timer_action)
        self.menu.addSeparator()
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.update_action)
        self.menu.addAction(self.startup_action)
        self.menu.addSeparator()
        self.menu.addAction(self.exit_action)

    # ── 状态同步 ───────────────────────────────────────────

    def _sync_state(self):
        self.set_flexible_mode(config_manager.is_flexible)
        self.set_run_on_startup(system_service.is_run_on_startup())

    def set_flexible_mode(self, is_flexible):
        self.flexible_action.setChecked(is_flexible)
        self.flexible_action.setText(
            f"Flexible Mode: {'On' if is_flexible else 'Off'}"
        )

    def set_run_on_startup(self, is_enabled):
        self.startup_action.setChecked(is_enabled)
        self.startup_action.setText(
            f"Run on Startup: {'On' if is_enabled else 'Off'}"
        )

    # ── 通知 ───────────────────────────────────────────────

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, duration=5000):
        self.tray_icon.showMessage(title, message, icon, duration)
