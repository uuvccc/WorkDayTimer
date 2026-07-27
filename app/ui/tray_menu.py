from PyQt5.QtWidgets import QMenu, QAction, QSystemTrayIcon, QMessageBox, QStyle
from PyQt5.QtGui import QIcon
import os

class TrayMenu:
    def __init__(self, icon_file, parent=None):
        self.parent = parent
        self.tray_icon = QSystemTrayIcon(parent)
        self._setup_icon(icon_file)
        self.menu = QMenu(parent)
        self._setup_menu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

    def _setup_icon(self, icon_file):
        if os.path.exists(icon_file):
            self.tray_icon.setIcon(QIcon(icon_file))
        else:
            self.tray_icon.setIcon(QStyle.SP_MessageBoxInformation)

    def _setup_menu(self):
        self.open_action = QAction("Open", self.parent)
        self.flexible_action = QAction("Flexible Mode: Off", self.parent)
        self.flexible_action.setCheckable(True)
        self.custom_timer_action = QAction("Custom Timer", self.parent)
        self.settings_action = QAction("Settings", self.parent)
        self.update_action = QAction("Update Application", self.parent)
        self.startup_action = QAction("Run on Startup: Off", self.parent)
        self.startup_action.setCheckable(True)
        self.exit_action = QAction("Exit", self.parent)

        self.menu.addAction(self.open_action)
        self.menu.addAction(self.flexible_action)
        self.menu.addAction(self.custom_timer_action)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.update_action)
        self.menu.addAction(self.startup_action)
        self.menu.addAction(self.exit_action)

    def set_flexible_mode(self, is_flexible):
        self.flexible_action.setChecked(is_flexible)
        self.flexible_action.setText(f"Flexible Mode: {'On' if is_flexible else 'Off'}")

    def set_run_on_startup(self, is_enabled):
        self.startup_action.setChecked(is_enabled)
        self.startup_action.setText(f"Run on Startup: {'On' if is_enabled else 'Off'}")

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, duration=5000):
        self.tray_icon.showMessage(title, message, icon, duration)