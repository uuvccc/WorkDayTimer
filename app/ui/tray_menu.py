from PyQt5.QtWidgets import QMenu, QAction, QSystemTrayIcon, QStyle, QApplication
from PyQt5.QtGui import QIcon
import os
from app.utils.logger import logger


class TrayMenu:
    def __init__(self, icon_file, parent=None):
        self.parent = parent
        self.tray_icon = QSystemTrayIcon(parent)
        self._setup_icon(icon_file)
        self.menu = QMenu(parent)
        self._setup_menu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        logger.info("Tray menu initialized and icon shown")

    def _setup_icon(self, icon_file):
        if os.path.exists(icon_file):
            self.tray_icon.setIcon(QIcon(icon_file))
            logger.debug(f"Tray icon set from: {icon_file}")
        else:
            # 找不到图标文件时用 Qt 框架内置的标准图标兜底。
            # 注意：不能写 QIcon(QStyle.SP_MessageBoxInformation) —— QIcon 没有
            # 接收 QStyle.StandardPixmap 的构造函数，那样会抛 TypeError 导致托盘
            # 图标建立失败。必须通过 QApplication.style().standardIcon() 获取。
            self.tray_icon.setIcon(
                QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))
            logger.warning(f"Tray icon file not found, using default: {icon_file}")

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
        logger.info(f"Tray message: [{title}] {message}")
        self.tray_icon.showMessage(title, message, icon, duration)
