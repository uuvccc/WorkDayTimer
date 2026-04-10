import datetime
import logging
import os
import random
import sys
import requests  # Add import for HTTP requests
import win32gui
import win32con
import multiprocessing
import threading

from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QFont, QIcon, QIntValidator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout, QDialog, QSystemTrayIcon, QMenu, QAction, QLineEdit, QProgressBar, QStyle

from config import (START_TIME_FILE, isFLEXIBLE, ICON_FILE, IMAGE_DIRECTORY, DEFAULT_TIMER_IMAGE,
    WINDOW_POSITION_X, WINDOW_POSITION_Y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT,
    DIALOG_POSITION_X, DIALOG_POSITION_Y, DIALOG_SIZE_WIDTH, DIALOG_SIZE_HEIGHT,
    FLEXIBLE_MODE_FILE)

# Configure logging
# Get the directory where the script or executable is located
base_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(base_dir, 'app.log')

logging.basicConfig(
    filename=log_file,  # Log file name in the application directory
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

        # Check for updates in a separate thread
        import threading
        update_thread = threading.Thread(target=self.check_for_updates, daemon=True)
        update_thread.start()

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        # Ensure the icon file exists
        if os.path.exists(ICON_FILE):
            self.tray_icon.setIcon(QIcon(ICON_FILE))
        else:
            # Use a default icon if the custom one doesn't exist
            self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))
            logging.warning(f"Icon file not found: {ICON_FILE}")
        
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

        # Add an update action to the tray menu
        update_action = QAction("Update Application", self)
        update_action.triggered.connect(self.update_application)
        self.menu.addAction(update_action)

        # Add a startup action to the tray menu
        self.startup_action = QAction(f"Run on Startup: {'On' if self.is_run_on_startup() else 'Off'}", self)
        self.startup_action.setCheckable(True)
        self.startup_action.setChecked(self.is_run_on_startup())
        self.startup_action.triggered.connect(self.toggle_run_on_startup)
        self.menu.addAction(self.startup_action)

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
        
        # Verify tray icon is visible
        if not self.tray_icon.isVisible():
            logging.warning("Tray icon is not visible")
            # Try to show it again
            self.tray_icon.show()

        # Set up global keyboard hook for Enter key
        self.setup_keyboard_hook()

    def init_ui(self):
        try:
            self.countdown_label = QLabel(self)
            # Enable key press events
            self.setFocusPolicy(Qt.StrongFocus)
            self.countdown_label.setPixmap(QPixmap(DEFAULT_TIMER_IMAGE).scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            # Enable context menu for the label
            self.countdown_label.setContextMenuPolicy(Qt.CustomContextMenu)
            self.countdown_label.customContextMenuRequested.connect(self.show_context_menu)
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.toggle_qq_window()

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
        # Stop keyboard listener before exiting
        import keyboard
        keyboard.unhook_all()
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

    def is_run_on_startup(self):
        """Check if the application is set to run on startup"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "WorkDayTimer")
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def toggle_run_on_startup(self):
        """Toggle run on startup setting"""
        is_enabled = self.startup_action.isChecked()
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            try:
                if is_enabled:
                    # Add to startup
                    exe_path = os.path.abspath(sys.argv[0])
                    winreg.SetValueEx(key, "WorkDayTimer", 0, winreg.REG_SZ, f'"{exe_path}"')
                    QMessageBox.information(self, "Startup Setting", "Application has been added to startup.")
                else:
                    # Remove from startup
                    winreg.DeleteValue(key, "WorkDayTimer")
                    QMessageBox.information(self, "Startup Setting", "Application has been removed from startup.")
            except FileNotFoundError:
                if not is_enabled:
                    # Already not in startup
                    QMessageBox.information(self, "Startup Setting", "Application is not in startup.")
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update startup setting: {e}")
            self.startup_action.setChecked(not is_enabled)

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

    def setup_keyboard_hook(self):
        """Set up a global keyboard hook to listen for Enter key press using multiprocessing"""
        import keyboard
        
        def on_enter_key(event):
            if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
                self.toggle_qq_window()
        
        # Register the hook in a separate thread
        self.keyboard_listener_thread = threading.Thread(target=self._start_keyboard_listener, daemon=True)
        self.keyboard_listener_thread.start()

    def _start_keyboard_listener(self):
        """Start the keyboard listener in a separate thread"""
        import keyboard
        
        def on_enter_key(event):
            if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
                # Use wx.CallAfter equivalent for Qt
                self.toggle_qq_window()
        
        # Start the keyboard listener
        keyboard.hook(on_enter_key)
        
        # Keep the thread alive
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass

    def toggle_qq_window(self):
        """Toggle visibility of windows with 'QQ..exe' in the title"""
        def window_enum_callback(hwnd, extra):
            if "QQ..exe" in win32gui.GetWindowText(hwnd):
                # Check if window is visible
                if win32gui.IsWindowVisible(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        
        win32gui.EnumWindows(window_enum_callback, None)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.toggle_qq_window()

    def show_context_menu(self, position):
        # Show the same menu as the tray icon
        self.menu.exec_(self.countdown_label.mapToGlobal(position))

    def shutdown_computer(self):
        # **WARNING:  Use with EXTREME caution!**  Add robust confirmation dialog before implementing.
        try:
            os.system("shutdown /s /t 1") #Windows shutdown command, adjust for other OS.
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Shutdown failed: {e}")

    def check_for_updates(self):
        """Check for updates from GitHub."""
        try:
            # Get current version from setup.py
            import setup
            current_version = setup.setup.version
            
            # Get latest version from GitHub API
            api_url = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                # Compare versions
                if self._is_newer_version(latest_version, current_version):
                    # Show update notification in the main thread
                    QApplication.postEvent(self, QEvent(QEvent.User))
        except Exception as e:
            # Silent error handling to avoid disrupting the app
            logging.error(f"Error checking for updates: {e}")
    
    def _is_newer_version(self, latest, current):
        """Compare version strings to determine if a new version is available."""
        try:
            # Split version strings into components
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            # Pad with zeros to make lengths equal
            max_length = max(len(latest_parts), len(current_parts))
            while len(latest_parts) < max_length:
                latest_parts.append(0)
            while len(current_parts) < max_length:
                current_parts.append(0)
            
            # Compare each component
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            return False
        except Exception:
            # If version parsing fails, assume no update
            return False
    
    def event(self, event):
        """Handle custom events, including update notifications."""
        if event.type() == QEvent.User:
            # Show update notification
            reply = QMessageBox.question(self, "Update Available", 
                                       "A new version of WorkDayTimer is available!\n" 
                                       "Do you want to update now?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.update_application()
            return True
        return super().event(event)

    def update_application(self):
        """Download the latest executable from GitHub and replace the current one."""
        try:
            github_url = "https://github.com/uuvccc/WorkDayTimer/releases/latest/download/WorkDayTimer.exe"
            
            # Determine if running as executable or script
            local_exe_path = sys.argv[0]
            is_running_as_exe = local_exe_path.endswith('.exe')
            
            if not is_running_as_exe:
                # When running as script, download to current directory
                local_exe_path = os.path.join(os.getcwd(), "WorkDayTimer.exe")
                reply = QMessageBox.question(self, "Update Confirmation", 
                                           "Application is running as a Python script.\n"
                                           "The executable will be downloaded to the current directory.\n"
                                           f"Download location: {local_exe_path}\n"
                                           "Do you want to continue?")
                if reply == QMessageBox.No:
                    return

            # Create a temporary file for the new version
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_exe_path = os.path.join(temp_dir, "WorkDayTimer_new.exe")

            # Create progress dialog - non-modal to allow user to continue using the app
            progress_dialog = QDialog(None)
            progress_dialog.setWindowTitle("Downloading Update")
            progress_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
            progress_dialog.setModal(False)  # Non-modal to allow user interaction with main app
            progress_dialog.resize(300, 120)
            
            layout = QVBoxLayout()
            label = QLabel("Downloading update...")
            layout.addWidget(label)
            
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            layout.addWidget(progress_bar)
            
            # Add cancel button
            cancel_button = QPushButton("Cancel")
            layout.addWidget(cancel_button)
            
            progress_dialog.setLayout(layout)
            progress_dialog.show()
            QApplication.processEvents()  # Ensure dialog is displayed

            # Flag to indicate if download was cancelled
            download_cancelled = False
            
            def cancel_download():
                nonlocal download_cancelled
                download_cancelled = True
                logging.info("Download cancelled by user")
            
            cancel_button.clicked.connect(cancel_download)

            # Download in a separate thread
            import threading
            download_success = False
            download_error = None
            
            def download_file():
                nonlocal download_success, download_error
                try:
                    # Set timeout for the request
                    response = requests.get(github_url, stream=True, timeout=30)
                    if response.status_code == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        
                        with open(temp_exe_path, "wb") as exe_file:
                            # Create a function to update UI safely
                            def update_ui(progress_value=None, status_text=None, indeterminate=False):
                                def do_update():
                                    if indeterminate:
                                        progress_bar.setRange(0, 0)
                                    elif progress_value is not None:
                                        progress_bar.setRange(0, 100)
                                        progress_bar.setValue(progress_value)
                                    if status_text is not None:
                                        label.setText(status_text)
                                QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                                QApplication.processEvents()
                            
                            if total_size == 0:
                                # If content-length header is missing, set indeterminate progress bar
                                update_ui(indeterminate=True, status_text="Downloading update... (size unknown)")
                            
                            for chunk in response.iter_content(chunk_size=4096):  # Use larger chunk size for faster download
                                if download_cancelled:
                                    logging.info("Download cancelled, closing connection")
                                    break
                                if chunk:
                                    exe_file.write(chunk)
                                    downloaded_size += len(chunk)
                                    if total_size > 0:
                                        progress = int((downloaded_size / total_size) * 100)
                                        # Update UI in main thread
                                        QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                                        progress_bar.setValue(progress)
                                        label.setText(f"Downloading update... {progress}%")
                                    else:
                                        # Update UI even when we don't know the total size
                                        QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                                        label.setText(f"Downloading update... {downloaded_size} bytes")
                                    QApplication.processEvents()
                        
                        if not download_cancelled:
                            download_success = True
                    else:
                        download_error = f"Failed to download the update. HTTP Status Code: {response.status_code}"
                        logging.error(download_error)
                except requests.exceptions.Timeout:
                    download_error = "Download timed out. Please check your network connection and try again."
                    logging.error(download_error)
                except requests.exceptions.RequestException as e:
                    download_error = f"Network error: {str(e)}"
                    logging.error(download_error)
                except Exception as e:
                    download_error = f"An error occurred: {str(e)}"
                    logging.error(download_error)
            
            # Start download thread
            download_thread = threading.Thread(target=download_file)
            download_thread.daemon = True
            download_thread.start()
            
            # Create a timer to check download status periodically
            status_check_timer = QTimer(self)
            
            def check_download_status():
                if not download_thread.is_alive():
                    status_check_timer.stop()
                    progress_dialog.close()
                    
                    if download_cancelled:
                        QMessageBox.information(self, "Update Cancelled", "The update download was cancelled.")
                    elif download_error:
                        QMessageBox.critical(self, "Update Failed", download_error)
                    elif not download_success:
                        QMessageBox.critical(self, "Update Failed", "Download failed for unknown reason.")
                    else:
                        # Download completed successfully, proceed with update
                        if not is_running_as_exe:
                            # If running as script, just move the downloaded file to current directory
                            import shutil
                            try:
                                shutil.move(temp_exe_path, local_exe_path)
                                QMessageBox.information(self, "Update Complete", 
                                                      f"Executable downloaded successfully!\n"
                                                      f"Location: {local_exe_path}\n"
                                                      f"Run this file to start the application as an executable.")
                            except Exception as e:
                                QMessageBox.critical(self, "Error", f"Failed to move downloaded file: {e}")
                        else:
                            # === RADICAL REWRITE: Professional updater implementation ===
                            # Create a fully independent updater that doesn't rely on Python
                            updater_batch = os.path.join(os.path.dirname(local_exe_path), "updater.bat")
                            
                            # Create a batch file with robust update logic
                            with open(updater_batch, "w") as f:
                                f.write(f"""@echo off
setlocal EnableDelayedExpansion

:: Set variables
set "OLD_EXE={local_exe_path}"
set "NEW_EXE={temp_exe_path}"
set "EXE_DIR={os.path.dirname(local_exe_path)}"
set "LOG_FILE=%EXE_DIR%\update.log"

:: Create log file
echo [%DATE% %TIME%] Updater started >> "%LOG_FILE%"
echo Old EXE: %OLD_EXE% >> "%LOG_FILE%"
echo New EXE: %NEW_EXE% >> "%LOG_FILE%"
echo EXE Directory: %EXE_DIR% >> "%LOG_FILE%"

:: Change to the executable directory
cd /d "%EXE_DIR%"
echo [%DATE% %TIME%] Changed to directory: %CD% >> "%LOG_FILE%"

:: Wait for the old process to fully exit
echo [%DATE% %TIME%] Waiting for old process to exit... >> "%LOG_FILE%"
timeout /t 10 /nobreak >nul

:: Kill any remaining instances
echo [%DATE% %TIME%] Killing any remaining instances... >> "%LOG_FILE%"
taskkill /f /im WorkDayTimer.exe 2>> "%LOG_FILE%"

:: Wait a bit more to ensure resources are released
echo [%DATE% %TIME%] Waiting for resources to be released... >> "%LOG_FILE%"
timeout /t 5 /nobreak >nul

:: Verify the new executable exists
if not exist "%NEW_EXE%" (
    echo [%DATE% %TIME%] ERROR: New executable not found >> "%LOG_FILE%"
    goto cleanup
)
echo [%DATE% %TIME%] New executable found >> "%LOG_FILE%"

:: Create backup of old executable
set "BACKUP_EXE=%OLD_EXE%.bak"
if exist "%OLD_EXE%" (
    echo [%DATE% %TIME%] Creating backup... >> "%LOG_FILE%"
    copy /y "%OLD_EXE%" "%BACKUP_EXE%" >> "%LOG_FILE%"
    if errorlevel 1 (
        echo [%DATE% %TIME%] ERROR: Failed to create backup >> "%LOG_FILE%"
        goto cleanup
    )
    echo [%DATE% %TIME%] Backup created: %BACKUP_EXE% >> "%LOG_FILE%"
)

:: Delete the old executable
echo [%DATE% %TIME%] Deleting old executable... >> "%LOG_FILE%"
del /f /q "%OLD_EXE%" 2>> "%LOG_FILE%"

:: Wait for deletion to complete
timeout /t 2 /nobreak >nul

:: Move the new executable
echo [%DATE% %TIME%] Moving new executable... >> "%LOG_FILE%"
move /y "%NEW_EXE%" "%OLD_EXE%" >> "%LOG_FILE%"
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Failed to move new executable >> "%LOG_FILE%"
    :: Try to restore from backup
    if exist "%BACKUP_EXE%" (
        echo [%DATE% %TIME%] Restoring from backup... >> "%LOG_FILE%"
        copy /y "%BACKUP_EXE%" "%OLD_EXE%" >> "%LOG_FILE%"
    )
    goto cleanup
)
echo [%DATE% %TIME%] New executable moved successfully >> "%LOG_FILE%"

:: Wait for move to complete
timeout /t 2 /nobreak >nul

:: Verify the new executable exists
if not exist "%OLD_EXE%" (
    echo [%DATE% %TIME%] ERROR: New executable not found after move >> "%LOG_FILE%"
    :: Try to restore from backup
    if exist "%BACKUP_EXE%" (
        echo [%DATE% %TIME%] Restoring from backup... >> "%LOG_FILE%"
        copy /y "%BACKUP_EXE%" "%OLD_EXE%" >> "%LOG_FILE%"
    )
    goto cleanup
)
echo [%DATE% %TIME%] New executable verified >> "%LOG_FILE%"

:: Set clean environment
set "PYTHONPATH="
set "PYTHONHOME="
set "PATH=C:\Windows\System32;C:\Windows\SysWOW64;%PATH%"
echo [%DATE% %TIME%] Environment variables set >> "%LOG_FILE%"

:: Start the new executable with clean environment
echo [%DATE% %TIME%] Starting new executable... >> "%LOG_FILE%"
start "" /D "%EXE_DIR%" "%OLD_EXE%"
if errorlevel 1 (
    echo [%DATE% %TIME%] ERROR: Failed to start new executable >> "%LOG_FILE%"
    goto cleanup
)
echo [%DATE% %TIME%] New executable started successfully >> "%LOG_FILE%"

:cleanup
:: Wait before cleanup
echo [%DATE% %TIME%] Waiting before cleanup... >> "%LOG_FILE%"
timeout /t 5 /nobreak >nul

:: Cleanup backup
if exist "%BACKUP_EXE%" (
    echo [%DATE% %TIME%] Cleaning up backup... >> "%LOG_FILE%"
    del /f /q "%BACKUP_EXE%" 2>> "%LOG_FILE%"
)

:: Cleanup this script
echo [%DATE% %TIME%] Cleaning up updater... >> "%LOG_FILE%"
timeout /t 1 /nobreak >nul
del /f /q "%~f0" 2>> "%LOG_FILE%"

:: Exit
echo [%DATE% %TIME%] Updater finished >> "%LOG_FILE%"
exit
""")
                            
                            # Launch the updater batch file and exit immediately
                            print(f"Launching robust updater batch: {updater_batch}")
                            import subprocess
                            
                            # Use CREATE_NEW_PROCESS_GROUP to ensure the batch file runs independently
                            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                            
                            # Launch the batch file with clean environment
                            env = os.environ.copy()
                            env['PATH'] = r"C:\Windows\System32;C:\Windows\SysWOW64;" + env.get('PATH', '')
                            
                            subprocess.Popen(
                                updater_batch, 
                                shell=True, 
                                env=env,
                                creationflags=creation_flags,
                                close_fds=True
                            )
                            
                            # Exit immediately to release all resources
                            import sys
                            sys.exit(0)
            
            status_check_timer.timeout.connect(check_download_status)
            status_check_timer.start(100)  # Check every 100ms
        except Exception as e:
            logging.error(f"Update error: {e}")
            if 'progress_dialog' in locals() and progress_dialog:
                progress_dialog.close()
            QMessageBox.critical(self, "Update Error", f"An error occurred during the update: {e}")


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        workday_timer = WorkdayTimer(app)
        sys.exit(app.exec_())
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        logging.error(error_message)  # Write error message to log
        
        # Create a simple tray icon for error reporting
        try:
            app = QApplication(sys.argv)
            tray_icon = QSystemTrayIcon()
            tray_icon.setIcon(QIcon(ICON_FILE))
            menu = QMenu()
            exit_action = QAction("Exit", None)
            exit_action.triggered.connect(app.quit)
            menu.addAction(exit_action)
            tray_icon.setContextMenu(menu)
            tray_icon.show()
            tray_icon.showMessage("WorkDayTimer Error", f"An error occurred: {e}", QSystemTrayIcon.Critical, 5000)
            sys.exit(app.exec_())
        except:
            pass


