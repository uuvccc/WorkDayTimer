from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from app.config.manager import config_manager
from app.services import system_service


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setMinimumWidth(320)
        self._setup_ui()
        self._load_settings()

    # ── UI 构建 ────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # ── 工作模式 ──
        mode_group = QGroupBox("Work Mode")
        mode_layout = QVBoxLayout()
        self.flexible_checkbox = QCheckBox("Flexible Mode (flexible work hours)")
        mode_layout.addWidget(self.flexible_checkbox)
        hint = QLabel("When enabled, work end time is calculated from your actual start time.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 11px;")
        mode_layout.addWidget(hint)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # ── 提醒设置 ──
        reminder_group = QGroupBox("Reminders")
        reminder_layout = QVBoxLayout()
        self.checkin_checkbox = QCheckBox("Check-in reminder on startup")
        self.job_record_checkbox = QCheckBox("Job record reminder (before end)")
        self.checkout_checkbox = QCheckBox("Check-out reminder at work end")
        reminder_layout.addWidget(self.checkin_checkbox)
        reminder_layout.addWidget(self.job_record_checkbox)
        reminder_layout.addWidget(self.checkout_checkbox)
        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)

        # ── 系统 ──
        system_group = QGroupBox("System")
        system_layout = QVBoxLayout()
        self.startup_checkbox = QCheckBox("Run on Windows startup")
        system_layout.addWidget(self.startup_checkbox)
        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # ── 按钮 ──
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self._on_ok)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    # ── 读写 ──────────────────────────────────────────────

    def _load_settings(self):
        self.flexible_checkbox.setChecked(config_manager.is_flexible)
        self.checkin_checkbox.setChecked(config_manager.get_reminder_setting("checkin_reminder"))
        self.job_record_checkbox.setChecked(config_manager.get_reminder_setting("job_record_reminder"))
        self.checkout_checkbox.setChecked(config_manager.get_reminder_setting("checkout_reminder"))
        self.startup_checkbox.setChecked(system_service.is_run_on_startup())

    def _on_ok(self):
        # 1) Flexible Mode
        old_flexible = config_manager.is_flexible
        new_flexible = self.flexible_checkbox.isChecked()
        config_manager.is_flexible = new_flexible

        # 2) Reminders
        config_manager.set_reminder_setting("checkin_reminder", self.checkin_checkbox.isChecked())
        config_manager.set_reminder_setting("job_record_reminder", self.job_record_checkbox.isChecked())
        config_manager.set_reminder_setting("checkout_reminder", self.checkout_checkbox.isChecked())

        # 3) Run on Startup
        new_startup = self.startup_checkbox.isChecked()
        success, msg = system_service.toggle_run_on_startup(new_startup)
        if not success:
            QMessageBox.critical(self, "Error", msg)
            self.startup_checkbox.setChecked(not new_startup)
            return

        self.accept()

        # 如果 flexible mode 变了，提示重启
        if old_flexible != new_flexible:
            QMessageBox.information(
                self, "Mode Changed",
                "Flexible mode has been " + ("enabled" if new_flexible else "disabled") + ".\n"
                "Please restart the application for the change to take effect.",
            )
