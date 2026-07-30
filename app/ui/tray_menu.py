from PyQt5.QtWidgets import QMenu, QAction, QSystemTrayIcon, QStyle
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
        # Show Window
        self.open_action = QAction("Show Window", self.parent)
        self.menu.addAction(self.open_action)

        self.menu.addSeparator()

        # Quick Action
        self.custom_timer_action = QAction("Custom Timer...", self.parent)
        self.menu.addAction(self.custom_timer_action)

        self.menu.addSeparator()

        # Settings
        self.settings_action = QAction("Settings...", self.parent)
        self.menu.addAction(self.settings_action)

        self.menu.addSeparator()

        # Quit
        self.exit_action = QAction("Quit", self.parent)
        self.menu.addAction(self.exit_action)

    def show_message(self, title, message, icon=QSystemTrayIcon.Information, duration=5000):
        self.tray_icon.showMessage(title, message, icon, duration)
