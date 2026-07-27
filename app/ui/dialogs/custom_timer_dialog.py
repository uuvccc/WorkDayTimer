from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtCore import Qt

class CustomTimerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Timer")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        self._result_minutes = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        input_label = QLabel("Enter minutes:")
        self.input_field = QLineEdit()
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setFont(QFont("Arial", 20))
        self.input_field.setText("0")
        self.input_field.setValidator(QIntValidator(0, 999999))
        layout.addWidget(input_label)
        layout.addWidget(self.input_field)

        quick_select_layout = QVBoxLayout()

        row1_layout = QHBoxLayout()
        for i in range(1, 6):
            btn = QPushButton(str(i))
            btn.clicked.connect(lambda checked, num=i: self._add_minutes(num))
            row1_layout.addWidget(btn)
        quick_select_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        for i in range(6, 11):
            btn = QPushButton(str(i))
            btn.clicked.connect(lambda checked, num=i: self._add_minutes(num))
            row2_layout.addWidget(btn)
        quick_select_layout.addLayout(row2_layout)

        row3_layout = QHBoxLayout()
        for minutes in [15, 20, 30]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self._add_minutes(num))
            row3_layout.addWidget(btn)
        quick_select_layout.addLayout(row3_layout)

        row4_layout = QHBoxLayout()
        for minutes in [40, 60, 90]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self._add_minutes(num))
            row4_layout.addWidget(btn)
        quick_select_layout.addLayout(row4_layout)

        row5_layout = QHBoxLayout()
        for minutes in [120, 180, 240]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self._add_minutes(num))
            row5_layout.addWidget(btn)
        quick_select_layout.addLayout(row5_layout)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.input_field.setText("0"))
        quick_select_layout.addWidget(clear_button)

        layout.addLayout(quick_select_layout)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self._on_ok)
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def _add_minutes(self, minutes):
        try:
            current = int(self.input_field.text())
            self.input_field.setText(str(current + minutes))
        except ValueError:
            self.input_field.setText(str(minutes))

    def _on_ok(self):
        try:
            minutes = int(self.input_field.text())
            if minutes > 0:
                self._result_minutes = minutes
                self.accept()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Invalid Input", "Please enter a positive number.")
        except ValueError:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")

    def get_minutes(self):
        return self._result_minutes