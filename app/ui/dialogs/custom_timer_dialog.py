from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtCore import Qt
from app.ui.dialogs.common import FancyDialog, quick_button_qss, ghost_button_qss
from app.utils.logger import logger


class CustomTimerDialog(FancyDialog):
    def __init__(self, parent=None):
        super().__init__("自定义计时器 · Custom Timer", "violet", parent)
        logger.debug("CustomTimerDialog opening")
        self._result_minutes = 0
        self._build_body()
        self._build_buttons()
        self._center_on_screen()

    # ── 内容区 ────────────────────────────────────────────

    def _build_body(self):
        emoji_label = QLabel("⏱️")
        emoji_label.setStyleSheet("font-size: 36px;")
        emoji_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(emoji_label)

        hint = QLabel("设置倒计时时长（分钟）\nEnter minutes below")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 13px;")
        self.content_layout.addWidget(hint)

        self.input_field = QLineEdit()
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setFont(QFont(self.font().family(), 22, QFont.Bold))
        self.input_field.setText("0")
        self.input_field.setValidator(QIntValidator(0, 999999))
        self.input_field.setStyleSheet(
            "QLineEdit { background: #ffffff; color: #333; border: none;"
            "  border-radius: 12px; padding: 10px 14px;"
            "  font-size: 24px; font-weight: bold; }"
            "QLineEdit:focus { border: 2px solid rgba(255,255,255,0.9); }"
        )
        self.content_layout.addWidget(self.input_field)

        self.content_layout.addSpacing(8)

        quick_layout = QVBoxLayout()
        quick_layout.setSpacing(8)
        rows = [
            range(1, 6),
            range(6, 11),
            [15, 20, 30],
            [40, 60, 90],
            [120, 180, 240],
        ]
        for values in rows:
            row = QHBoxLayout()
            row.setSpacing(8)
            for minutes in values:
                btn = self.make_button(str(minutes), quick_button_qss())
                btn.clicked.connect(lambda checked, num=minutes: self._add_minutes(num))
                row.addWidget(btn)
            quick_layout.addLayout(row)
        self.content_layout.addLayout(quick_layout)

    # ── 底部按钮行 ───────────────────────────────────────

    def _build_buttons(self):
        clear_btn = self.make_button(
            "清零 Clear", ghost_button_qss(),
            on_click=lambda: self.input_field.setText("0"),
        )
        start_btn = self.make_primary_button("开始 Start", on_click=self._on_ok)
        cancel_btn = self.make_button("取消 Cancel", ghost_button_qss(), on_click=self.reject)

        self.button_layout.addWidget(clear_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(start_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(cancel_btn)

    # ── 逻辑（保持不变）──────────────────────────────────

    def _add_minutes(self, minutes):
        try:
            current = int(self.input_field.text())
            new_val = current + minutes
            self.input_field.setText(str(new_val))
            logger.debug(f"Added {minutes} minutes, total now: {new_val}")
        except ValueError:
            self.input_field.setText(str(minutes))
            logger.debug(f"Invalid input, reset to {minutes} minutes")

    def _on_ok(self):
        try:
            minutes = int(self.input_field.text())
            if minutes > 0:
                self._result_minutes = minutes
                logger.info(f"Custom timer set: {minutes} minutes")
                self.accept()
            else:
                logger.warning(f"Custom timer invalid input: {minutes} (must be positive)")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Input", "Please enter a positive number.")
        except ValueError:
            logger.warning(f"Custom timer non-numeric input: '{self.input_field.text()}'")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

    def get_minutes(self):
        return self._result_minutes
