import datetime
import logging
import os
import random
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QSystemTrayIcon, QMenu, QAction

from config import (START_TIME_FILE, isFLEXIBLE, ICON_FILE, IMAGE_DIRECTORY, DEFAULT_TIMER_IMAGE,
    WINDOW_POSITION_X, WINDOW_POSITION_Y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT,
    DIALOG_POSITION_X, DIALOG_POSITION_Y, DIALOG_SIZE_WIDTH, DIALOG_SIZE_HEIGHT)

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

        # Countdown display
        self.time_label.setText('           : {:.0f} ✔ {}'.format(seconds, self.timer_expiry.minute))
        self.time_label.adjustSize()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

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

    def icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.moveAvatar()

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


