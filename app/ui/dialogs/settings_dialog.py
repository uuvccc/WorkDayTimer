from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from app.config.manager import config_manager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self.resize(300, 250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Reminder Settings"))

        settings = config_manager.reminder_settings

        self.checkin_button = QPushButton(f"Check-in Reminder: {'On' if settings['checkin_reminder'] else 'Off'}")
        self.checkin_button.setCheckable(True)
        self.checkin_button.setChecked(settings['checkin_reminder'])
        self.checkin_button.clicked.connect(lambda checked: self._toggle_setting('checkin_reminder', checked))
        layout.addWidget(self.checkin_button)

        self.job_record_button = QPushButton(f"Work Record Reminder: {'On' if settings['job_record_reminder'] else 'Off'}")
        self.job_record_button.setCheckable(True)
        self.job_record_button.setChecked(settings['job_record_reminder'])
        self.job_record_button.clicked.connect(lambda checked: self._toggle_setting('job_record_reminder', checked))
        layout.addWidget(self.job_record_button)

        self.checkout_button = QPushButton(f"Check-out Reminder: {'On' if settings['checkout_reminder'] else 'Off'}")
        self.checkout_button.setCheckable(True)
        self.checkout_button.setChecked(settings['checkout_reminder'])
        self.checkout_button.clicked.connect(lambda checked: self._toggle_setting('checkout_reminder', checked))
        layout.addWidget(self.checkout_button)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def _toggle_setting(self, key, is_checked):
        config_manager.set_reminder_setting(key, is_checked)
        if key == 'checkin_reminder':
            self.checkin_button.setText(f"Check-in Reminder: {'On' if is_checked else 'Off'}")
        elif key == 'job_record_reminder':
            self.job_record_button.setText(f"Work Record Reminder: {'On' if is_checked else 'Off'}")
        elif key == 'checkout_reminder':
            self.checkout_button.setText(f"Check-out Reminder: {'On' if is_checked else 'Off'}")