from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from app.utils.logger import logger

class ReminderDialog:
    @staticmethod
    def show_checkin(parent=None):
        logger.debug("Showing check-in reminder dialog")
        dialog = QMessageBox(parent)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        dialog.setWindowTitle("Microsoft Visual Studio")
        dialog.setText("checkin")
        dialog.setIcon(QMessageBox.Critical)
        dialog.addButton(QMessageBox.Close)
        dialog.setGeometry(700, 500, 900, 700)
        dialog.exec_()

    @staticmethod
    def show_job_record(parent=None):
        logger.debug("Showing job record reminder dialog")
        dialog = QMessageBox(parent)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dialog.setWindowTitle("Work Record Reminder")
        dialog.setText("Please remember to record your work progress!")
        dialog.setIcon(QMessageBox.Information)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec_()

    @staticmethod
    def show_checkout(parent=None, is_flexible=True, shutdown_callback=None):
        logger.debug(f"Showing checkout reminder dialog: is_flexible={is_flexible}, has_shutdown_cb={shutdown_callback is not None}")
        dialog = QMessageBox(parent)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dialog.setWindowTitle("Microsoft Visual Studio")

        if not is_flexible:
            reminder_message = "Need to shutdown"
        else:
            reminder_message = """Reminder:
        - 1. Clock out
        - 2. Turn off AC, water dispenser, windows, computer
        - 3. Write work log
        -- """

        dialog.setText(reminder_message)
        dialog.setIcon(QMessageBox.Information)

        if not is_flexible and shutdown_callback:
            shutdown_button = QPushButton("Shutdown")
            shutdown_button.clicked.connect(shutdown_callback)
            dialog.addButton(shutdown_button, QMessageBox.ActionRole)

        dialog.addButton(QMessageBox.Ignore)

        dialog.setMinimumSize(400, 200)
        dialog.setGeometry(700, 500, 750, 550)

        font = QFont()
        font.setPointSize(12)
        dialog.setFont(font)
        dialog.exec_()

    @staticmethod
    def show_custom_timer(parent=None):
        logger.debug("Showing custom timer reminder dialog")
        dialog = QMessageBox(parent)
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dialog.setWindowTitle("Custom Timer")
        dialog.setText("Custom timer countdown finished!")
        dialog.setIcon(QMessageBox.Information)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec_()

    @staticmethod
    def show_update_available(parent=None):
        from PyQt5.QtWidgets import QMessageBox
        logger.debug("Showing update available dialog")
        reply = QMessageBox.question(parent, "Update Available",
                                     "A new version of MiniTools is available!\n"
                                     "Do you want to update now?",
                                     QMessageBox.Yes | QMessageBox.No)
        return reply == QMessageBox.Yes