from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtCore import Qt, pyqtSignal
from app.ui.dialogs.common import (
    LightDialog,
    light_ghost_button_qss,
    light_quick_button_qss,
)
from app.utils.logger import logger


class CustomTimerDialog(LightDialog):
    """自定义计时器设置对话框（浅色非模态）。

    非模态下不再通过 exec_() 返回值，而是通过 timer_started 信号
    把用户设置的分钟数发给主窗口。
    """

    timer_started = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("自定义计时器 · Custom Timer", parent)
        logger.debug("CustomTimerDialog opening")
        self._result_minutes = 0
        self._build_body()
        self._build_buttons()

    # ── 内容区 ────────────────────────────────────────────

    def _build_body(self):
        emoji_label = QLabel("⏱️")
        emoji_label.setStyleSheet("font-size: 44px;")
        emoji_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(emoji_label)

        hint = QLabel("设置倒计时时长（分钟）\nEnter minutes below")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: #666666; font-size: 13px;")
        self.content_layout.addWidget(hint)

        self.input_field = QLineEdit()
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setFont(QFont(self.font().family(), 22, QFont.Bold))
        self.input_field.setText("0")
        self.input_field.setValidator(QIntValidator(0, 999999))
        self.input_field.setStyleSheet(
            "QLineEdit { background: #ffffff; color: #333333;"
            "  border: 1px solid #dddddd; border-radius: 12px;"
            "  padding: 10px 14px; font-size: 24px; font-weight: bold; }"
            "QLineEdit:focus { border: 2px solid #4CAF50; }"
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
                btn = QPushButton(str(minutes))
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(light_quick_button_qss())
                btn.clicked.connect(lambda checked, num=minutes: self._add_minutes(num))
                row.addWidget(btn)
            quick_layout.addLayout(row)
        self.content_layout.addLayout(quick_layout)

    # ── 底部按钮行 ───────────────────────────────────────

    def _build_buttons(self):
        clear_btn = QPushButton("清零 Clear")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(light_ghost_button_qss())
        clear_btn.clicked.connect(lambda: self.input_field.setText("0"))

        start_btn = self.make_primary_button("开始 Start", on_click=self._on_ok)
        cancel_btn = self.make_button("取消 Cancel", on_click=self.reject)

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
                self.timer_started.emit(minutes)
                self.accept()
            else:
                logger.warning(f"Custom timer invalid input: {minutes} (must be positive)")
                QMessageBox.warning(self, "Invalid Input", "Please enter a positive number.")
        except ValueError:
            logger.warning(f"Custom timer non-numeric input: '{self.input_field.text()}'")
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

    def get_minutes(self):
        return self._result_minutes
