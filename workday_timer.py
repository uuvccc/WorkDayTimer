import datetime
import logging
import os
import random
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QSystemTrayIcon, QMenu, QAction, QLineEdit

from config import (START_TIME_FILE, isFLEXIBLE, ICON_FILE, IMAGE_DIRECTORY, DEFAULT_TIMER_IMAGE,
    WINDOW_POSITION_X, WINDOW_POSITION_Y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT,
    DIALOG_POSITION_X, DIALOG_POSITION_Y, DIALOG_SIZE_WIDTH, DIALOG_SIZE_HEIGHT,
    FLEXIBLE_MODE_FILE)

# Configure logging
logging.basicConfig(
    filename='app.log',  # Log file name
    level=logging.DEBUG,  # Only record logs at DEBUG level and above
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

def get_last_start_time():
    """Reads the last start time from the config file. Returns None if not found."""
    try:
        with open(START_TIME_FILE, "r") as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                try:
                    return datetime.datetime.strptime(last_line, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    print("Warning: Invalid date format in config file. Using current time.")
                    return None
            else:
                return None
    except FileNotFoundError:
        return None


def write_start_time(start_time):
    """Writes the start time to the config file."""
    try:
        with open(START_TIME_FILE, "a") as f:
            f.write(start_time.strftime("%Y-%m-%d %H:%M:%S.%f") + "\n")
    except Exception as e:
        print(f"Error writing to config file: {e}")

class WorkdayTimer(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_ui()

        current_time = datetime.datetime.now()
        last_start_time = get_last_start_time()

        is_first_start = False
        if last_start_time is None or last_start_time.date() != current_time.date():
            # First start of the day
            print("First start of the day.")
            is_first_start = True
            write_start_time(current_time)
            last_start_time = current_time

        # Subtract 90 seconds
        last_start_time = last_start_time - datetime.timedelta(seconds=92) # < 94 95 100
        if not isFLEXIBLE:
            # Get current time
            now = datetime.datetime.now()
            # Create a time object representing 9 AM
            morning_nine = datetime.time(9, 0)
            # Combine current date with 9 AM time
            last_start_time = datetime.datetime.combine(now.date(), morning_nine)

        # Round down to the nearest minute
        last_start_time = last_start_time.replace(second=0, microsecond=0)
        self.timer_expiry = last_start_time + datetime.timedelta(hours=8.5)
        delay = (self.timer_expiry - datetime.datetime.now()).total_seconds()
        self.timer_type = delay

        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.show_reminder)
        self.reminder_timer.setSingleShot(True) # Only run once
        self.reminder_timer.start(int(delay * 1000)) # 8.5 hours in milliseconds

        timer_expiry2 = last_start_time + datetime.timedelta(hours=7.5)
        delay2 = (timer_expiry2 - datetime.datetime.now()).total_seconds()

        self.reminder_timer2 = QTimer()
        self.reminder_timer2.timeout.connect(self.show_job_record_warning)
        self.reminder_timer.setSingleShot(True) # Only run once
        self.reminder_timer2.start(int(delay2 * 1000)) # 8.5 hours in milliseconds

        if is_first_start:
            self.show_checkin_reminder()

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(ICON_FILE))  # Replace with your own icon file
        # Create menu for open and exit
        self.menu = QMenu()
        # Create action to open window
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.moveAvatar)
        self.menu.addAction(open_action)

        # Create action to toggle flexible mode
        self.flexible_action = QAction(f"Flexible Mode: {'On' if isFLEXIBLE else 'Off'}", self)
        self.flexible_action.setCheckable(True)
        self.flexible_action.setChecked(isFLEXIBLE)
        self.flexible_action.triggered.connect(self.toggle_flexible_mode)
        self.menu.addAction(self.flexible_action)

        # Create action for custom timer
        custom_timer_action = QAction("Custom Timer", self)
        custom_timer_action.triggered.connect(self.show_custom_timer_dialog)
        self.menu.addAction(custom_timer_action)

        # Create action to exit program
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(exit_action)
        # Set menu to system tray icon
        self.tray_icon.setContextMenu(self.menu)
        # Show system tray icon
        self.tray_icon.show()
        # Connect tray icon click event
        self.tray_icon.activated.connect(self.icon_activated)


    def init_ui(self):
        try:
            self.countdown_label = QLabel(self)
            self.countdown_label.setPixmap(QPixmap(DEFAULT_TIMER_IMAGE).scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Timer icon not found. Please check the path.")
            sys.exit(1)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_timer_display)
        self.display_timer.start(100)

        self.time_label = QLabel('Countdown: {}'.format(0), self)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.setParent(None)
        self.setGeometry(WINDOW_POSITION_X, WINDOW_POSITION_Y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)

    def update_timer_display(self):
        # Display image
        seconds = self.reminder_timer.remainingTime() / 1000.0

        # Add display for custom timer remaining time
        custom_timer_seconds = 0
        if hasattr(self, 'custom_timer') and self.custom_timer and self.custom_timer.isActive():
            custom_timer_seconds = self.custom_timer.remainingTime() / 1000.0

        if self.timer_type - seconds > 60:
            self.timer_type = seconds
            # Define image directory
            image_directory = IMAGE_DIRECTORY

            # List all image files in directory
            all_images = [f for f in os.listdir(image_directory) if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            # Randomly select an image
            if all_images:  # Make sure there are images in the directory
                random_image = random.choice(all_images)
                image_path = os.path.join(image_directory, random_image)
                self.countdown_label.setPixmap(QPixmap(image_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Update display text with both timer information
        display_text = '           : {:.0f} ✔ {}\n'.format(seconds, self.timer_expiry.minute)
        if custom_timer_seconds > 0:
            display_text += '           : {:.0f}s'.format(custom_timer_seconds)
        
        self.time_label.setText(display_text)
        self.time_label.adjustSize()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def show_checkin_reminder(self):
        job_record_reminder_dialog = QMessageBox()
        job_record_reminder_dialog.setWindowFlags(Qt.WindowStaysOnTopHint)
        job_record_reminder_dialog.setWindowTitle("Microsoft Visual Studio")
        reminder_message = """checkin"""

        job_record_reminder_dialog.setText(reminder_message)
        job_record_reminder_dialog.setIcon(QMessageBox.Critical)
        job_record_reminder_dialog.addButton(QMessageBox.Close) 
        job_record_reminder_dialog.setGeometry(700, 500, 900, 700)
        job_record_reminder_dialog.exec_()

    def show_reminder(self):
        reminder_dialog = QMessageBox()
        reminder_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        reminder_dialog.setWindowTitle("Microsoft Visual Studio")
        reminder_message = """Reminder:
        - 1. Clock out
        - 2. Turn off AC, water dispenser, windows, computer
        - 3. Write work log
        -- """
        if not isFLEXIBLE:
            reminder_message = """ Need to shutdown """

        reminder_dialog.setText(reminder_message)
        reminder_dialog.setIcon(QMessageBox.Information)
        
        # Add Shutdown Button
        shutdown_button = QPushButton("Shutdown")
        shutdown_button.clicked.connect(self.shutdown_computer)
        reminder_dialog.addButton(shutdown_button, QMessageBox.ActionRole)
        reminder_dialog.addButton(QMessageBox.Ignore)

        reminder_dialog.setMinimumSize(400, 200)
        desktop = QApplication.desktop()
        x = (desktop.width() - reminder_dialog.width()) // 2
        y = (desktop.height() - reminder_dialog.height()) // 2
        reminder_dialog.setGeometry(x, y, reminder_dialog.width(), reminder_dialog.height())
        reminder_dialog.setGeometry(DIALOG_POSITION_X, DIALOG_POSITION_Y, DIALOG_SIZE_WIDTH, DIALOG_SIZE_HEIGHT)

        font = QFont()
        font.setPointSize(12)
        reminder_dialog.setFont(font)
        reminder_dialog.exec()

    def show_job_record_warning(self):
        reminder_dialog = QMessageBox()
        reminder_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        reminder_dialog.setWindowTitle("Work Record Reminder")
        reminder_dialog.setText("Please remember to record your work progress!")
        reminder_dialog.setIcon(QMessageBox.Information)
        reminder_dialog.addButton(QMessageBox.Ok)
        reminder_dialog.exec()

    def moveAvatar(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        self.app.quit()

    def closeEvent(self, event):
        event.ignore()



    def icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.moveAvatar()

    def toggle_flexible_mode(self):
        """Toggle flexible mode and save the state to file"""
        is_flexible = self.flexible_action.isChecked()
        try:
            with open(FLEXIBLE_MODE_FILE, "w") as f:
                f.write(str(is_flexible).lower())
            global isFLEXIBLE
            isFLEXIBLE = is_flexible
            QMessageBox.information(self, "Mode Changed", "Flexible mode has been " + ("enabled" if is_flexible else "disabled") + ".\nPlease restart the application for the changes to take effect.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save flexible mode: {e}")
            self.flexible_action.setChecked(not is_flexible)

    def show_custom_timer_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Custom Timer")
        dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        layout = QVBoxLayout()

        # Create input field
        input_label = QLabel("Enter minutes:")
        input_field = QLineEdit()
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setFont(QFont("Arial", 20))
        input_field.setText("0")
        input_field.setValidator(QIntValidator(0, 999999))
        layout.addWidget(input_label)
        layout.addWidget(input_field)

        # Create quick select buttons layout
        quick_select_layout = QVBoxLayout()

        # First row - 1 to 5 minutes
        row1_layout = QHBoxLayout()
        for i in range(1, 6):
            btn = QPushButton(str(i))
            btn.clicked.connect(lambda checked, num=i: self.add_minutes(input_field, num))
            row1_layout.addWidget(btn)
        quick_select_layout.addLayout(row1_layout)

        # Second row - 6 to 10 minutes
        row2_layout = QHBoxLayout()
        for i in range(6, 11):
            btn = QPushButton(str(i))
            btn.clicked.connect(lambda checked, num=i: self.add_minutes(input_field, num))
            row2_layout.addWidget(btn)
        quick_select_layout.addLayout(row2_layout)

        # Third row - 15, 20, 30 minutes
        row3_layout = QHBoxLayout()
        for minutes in [15, 20, 30]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self.add_minutes(input_field, num))
            row3_layout.addWidget(btn)
        quick_select_layout.addLayout(row3_layout)

        # Fourth row - 40, 60, 90 minutes
        row4_layout = QHBoxLayout()
        for minutes in [40, 60, 90]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self.add_minutes(input_field, num))
            row4_layout.addWidget(btn)
        quick_select_layout.addLayout(row4_layout)

        # Fifth row - 120, 180, 240 minutes
        row5_layout = QHBoxLayout()
        for minutes in [120, 180, 240]:
            btn = QPushButton(f"{minutes}")
            btn.clicked.connect(lambda checked, num=minutes: self.add_minutes(input_field, num))
            row5_layout.addWidget(btn)
        quick_select_layout.addLayout(row5_layout)

        # Add clear button
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: input_field.setText("0"))
        quick_select_layout.addWidget(clear_button)

        layout.addLayout(quick_select_layout)

        # Create OK and Cancel buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        def start_custom_timer():
            try:
                minutes = int(input_field.text())
                if minutes > 0:
                    self.start_custom_countdown(minutes)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Invalid Input", "Please enter a positive number.")
            except ValueError:
                QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid number.")

        ok_button.clicked.connect(start_custom_timer)
        cancel_button.clicked.connect(dialog.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        dialog.setLayout(layout)
        dialog.exec_()

    def add_minutes(self, input_field, minutes):
        try:
            current = int(input_field.text())
            input_field.setText(str(current + minutes))
        except ValueError:
            input_field.setText(str(minutes))

    def start_custom_countdown(self, minutes):
        if hasattr(self, 'custom_timer'):
            self.custom_timer.stop()

        self.custom_timer = QTimer(self)
        self.custom_timer.timeout.connect(lambda: self.show_custom_timer_reminder())
        self.custom_timer.setSingleShot(True)
        self.custom_timer.start(minutes * 60 * 1000)

    def show_custom_timer_reminder(self):
        reminder_dialog = QMessageBox()
        reminder_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        reminder_dialog.setWindowTitle("Custom Timer")
        reminder_dialog.setText("Custom timer countdown finished!")
        reminder_dialog.setIcon(QMessageBox.Information)
        reminder_dialog.addButton(QMessageBox.Ok)
        reminder_dialog.exec_()

    def shutdown_computer(self):
        # **WARNING:  Use with EXTREME caution!**  Add robust confirmation dialog before implementing.
        try:
            os.system("shutdown /s /t 1") #Windows shutdown command, adjust for other OS.
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Shutdown failed: {e}")


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        workday_timer = WorkdayTimer(app)
        sys.exit(app.exec_())
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        logging.error(error_message)  # Write error message to log
        
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.icon_activated)

        # Initialize custom countdown timer
        self.custom_timer = None


