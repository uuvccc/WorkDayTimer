import os
import random
import datetime
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QMessageBox, QApplication, QDialog, QSystemTrayIcon

from app.config.constants import (
    ICON_FILE, IMAGE_DIRECTORY, DEFAULT_TIMER_IMAGE,
    WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT
)
from app.config.manager import config_manager
from app.services import time_service, system_service, update_service, keyboard_service
from app.ui import TrayMenu, SettingsDialog, CustomTimerDialog, ReminderDialog
from app.utils.logger import logger

class MainWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        logger.debug("MainWindow.__init__ start")
        self._setup_ui()
        self._setup_timers()
        self._setup_tray_menu()
        self._setup_keyboard_hook()
        self._check_for_updates()
        logger.info("MainWindow initialization complete")

    def _setup_ui(self):
        try:
            logger.debug("Setting up UI components")
            self.countdown_label = QLabel(self)
            self.setFocusPolicy(Qt.StrongFocus)
            self.countdown_label.setPixmap(QPixmap(DEFAULT_TIMER_IMAGE).scaled(
                60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            self.countdown_label.setContextMenuPolicy(Qt.CustomContextMenu)
            self.countdown_label.customContextMenuRequested.connect(self.show_context_menu)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Timer icon not found. Please check the path.")
            import sys
            sys.exit(1)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_timer_display)
        self.display_timer.start(100)
        logger.debug("Display timer started (100ms interval)")

        self.time_label = QLabel('Countdown: {}'.format(0), self)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.setParent(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        screen_rect = QApplication.primaryScreen().availableGeometry()
        x = screen_rect.right() - WINDOW_SIZE_WIDTH - 10
        y = screen_rect.top() + 10
        self.setGeometry(x, y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()
        logger.debug(f"Window positioned at ({x}, {y}), size=({WINDOW_SIZE_WIDTH}x{WINDOW_SIZE_HEIGHT})")

    def _setup_timers(self):
        current_time = datetime.datetime.now()
        is_first_start = time_service.is_first_start_of_day()
        logger.info(f"Timer setup | now={current_time.strftime('%H:%M:%S')} | is_first_start={is_first_start}")

        if is_first_start:
            time_service.write_start_time(current_time)

        is_flexible = config_manager.is_flexible
        _, work_end_time, job_record_time = time_service.calculate_work_end_time(
            start_time=current_time, is_flexible=is_flexible
        )

        self.timer_expiry = work_end_time
        logger.info(f"Timer setup: now={current_time.strftime('%H:%M')}, "
                     f"flexible={is_flexible}, work_end={work_end_time.strftime('%H:%M')}")

        checkout_enabled = config_manager.get_reminder_setting('checkout_reminder')
        if checkout_enabled:
            delay = time_service.calculate_remaining_seconds(work_end_time)
            self.timer_type = delay
            logger.info(f"Checkout reminder enabled, delay={delay:.0f}s "
                        f"({delay/60:.1f}min)")
            self.reminder_timer = QTimer(self)
            self.reminder_timer.timeout.connect(self.show_checkout_reminder)
            self.reminder_timer.setSingleShot(True)
            self.reminder_timer.start(int(delay * 1000))
        else:
            logger.info("Checkout reminder is DISABLED in settings")

        job_record_enabled = config_manager.get_reminder_setting('job_record_reminder')
        if job_record_enabled:
            delay2 = time_service.calculate_remaining_seconds(job_record_time)
            self.reminder_timer2 = QTimer(self)
            self.reminder_timer2.timeout.connect(self.show_job_record_warning)
            self.reminder_timer2.setSingleShot(True)
            self.reminder_timer2.start(int(delay2 * 1000))

        if is_first_start and config_manager.get_reminder_setting('checkin_reminder'):
            self.show_checkin_reminder()

    def _setup_tray_menu(self):
        logger.debug("Setting up tray menu")
        self.tray_menu = TrayMenu(ICON_FILE, self)
        self.tray_menu.open_action.triggered.connect(self.move_to_front)
        self.tray_menu.custom_timer_action.triggered.connect(self.show_custom_timer_dialog)
        self.tray_menu.settings_action.triggered.connect(self.show_settings_dialog)
        self.tray_menu.exit_action.triggered.connect(self.exit_app)
        self.tray_menu.tray_icon.activated.connect(self.on_tray_icon_activated)

    def _setup_keyboard_hook(self):
        logger.debug("Setting up keyboard hook")
        keyboard_service.set_enter_key_callback(self.toggle_qq_window)
        keyboard_service.start_listening()

    def _check_for_updates(self):
        import threading
        update_thread = threading.Thread(target=self._do_check_updates, daemon=True)
        update_thread.start()

    def _do_check_updates(self):
        logger.debug("Checking for updates in background thread")
        try:
            has_update, latest_version, current_version = update_service.check_for_updates()
            logger.info(f"Update check result: has_update={has_update}, latest={latest_version}, current={current_version}")
            if has_update:
                QApplication.postEvent(self, QEvent(QEvent.User))
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)

    def update_timer_display(self):
        seconds = 0
        if hasattr(self, 'reminder_timer') and self.reminder_timer and self.reminder_timer.isActive():
            seconds = self.reminder_timer.remainingTime() / 1000.0

        custom_timer_seconds = 0
        if hasattr(self, 'custom_timer') and self.custom_timer and self.custom_timer.isActive():
            custom_timer_seconds = self.custom_timer.remainingTime() / 1000.0

        if hasattr(self, 'timer_type') and self.timer_type - seconds > 60:
            self.timer_type = seconds
            all_images = [f for f in os.listdir(IMAGE_DIRECTORY) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if all_images:
                random_image = random.choice(all_images)
                image_path = os.path.join(IMAGE_DIRECTORY, random_image)
                self.countdown_label.setPixmap(QPixmap(image_path).scaled(
                    60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        display_text = '           : {:.0f} ✔ {}\n'.format(seconds, self.timer_expiry.minute)
        if custom_timer_seconds > 0:
            display_text += '           : {:.0f}s'.format(custom_timer_seconds)

        self.time_label.setText(display_text)
        self.time_label.adjustSize()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    def show_checkin_reminder(self):
        logger.info("Showing check-in reminder dialog")
        ReminderDialog.show_checkin(self)

    def show_job_record_warning(self):
        logger.info("Showing job record reminder dialog")
        ReminderDialog.show_job_record(self)

    def show_checkout_reminder(self):
        logger.info("Checkout reminder triggered!")
        is_flexible = config_manager.is_flexible
        logger.info(f"Checkout reminder: is_flexible={is_flexible}")
        ReminderDialog.show_checkout(self, is_flexible, self.shutdown_computer)

    def show_custom_timer_dialog(self):
        logger.debug("Opening custom timer dialog")
        dialog = CustomTimerDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            minutes = dialog.get_minutes()
            logger.info(f"Custom timer dialog accepted: {minutes} minutes")
            if minutes > 0:
                self.start_custom_countdown(minutes)
        else:
            logger.debug("Custom timer dialog cancelled")

    def show_settings_dialog(self):
        logger.debug("Opening settings dialog")
        dialog = SettingsDialog(self, update_callback=self.update_application)
        dialog.exec_()
        logger.debug("Settings dialog closed")

    def start_custom_countdown(self, minutes):
        logger.info(f"Starting custom countdown: {minutes} minutes")
        if hasattr(self, 'custom_timer'):
            self.custom_timer.stop()
            logger.debug("Stopped previous custom timer")

        self.custom_timer = QTimer(self)
        self.custom_timer.timeout.connect(self.show_custom_timer_reminder)
        self.custom_timer.setSingleShot(True)
        self.custom_timer.start(minutes * 60 * 1000)

    def show_custom_timer_reminder(self):
        logger.info("Custom timer expired, showing reminder")
        ReminderDialog.show_custom_timer(self)

    def update_application(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton

        local_exe_path, is_running_as_exe = update_service.get_download_path()

        if not is_running_as_exe:
            reply = QMessageBox.question(self, "Update Confirmation",
                                         "Application is running as a Python script.\n"
                                         "The executable will be downloaded to the current directory.\n"
                                         f"Download location: {local_exe_path}\n"
                                         "Do you want to continue?")
            if reply == QMessageBox.No:
                return

        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("Downloading Update")
        progress_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        progress_dialog.setModal(False)
        progress_dialog.resize(300, 120)

        layout = QVBoxLayout()
        label = QLabel("Downloading update...")
        layout.addWidget(label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)

        cancel_button = QPushButton("Cancel")
        layout.addWidget(cancel_button)

        progress_dialog.setLayout(layout)
        progress_dialog.show()
        QApplication.processEvents()

        download_cancelled = False

        def cancel_download():
            nonlocal download_cancelled
            download_cancelled = True

        cancel_button.clicked.connect(cancel_download)

        download_success = False
        download_error = None
        temp_exe_path = None

        def download_file():
            nonlocal download_success, download_error, temp_exe_path
            result = update_service.download_update(
                progress_callback=lambda progress, text: self._update_progress(progress_bar, label, progress, text)
            )
            download_success, temp_exe_path, download_error = result

        import threading
        download_thread = threading.Thread(target=download_file, daemon=True)
        download_thread.start()

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
                    self._complete_update(temp_exe_path, local_exe_path, is_running_as_exe)

        status_check_timer.timeout.connect(check_download_status)
        status_check_timer.start(100)

    def _update_progress(self, progress_bar, label, progress, text):
        if progress is not None:
            progress_bar.setRange(0, 100)
            progress_bar.setValue(progress)
        else:
            progress_bar.setRange(0, 0)
        if text:
            label.setText(text)
        QApplication.processEvents()

    def _complete_update(self, temp_exe_path, local_exe_path, is_running_as_exe):
        if not is_running_as_exe:
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
            updater_script = update_service.prepare_updater_script(temp_exe_path, local_exe_path)
            if updater_script:
                update_service.run_updater(updater_script)
                self.exit_app()
            else:
                QMessageBox.critical(self, "Error", "Failed to prepare updater script.")

    def toggle_qq_window(self):
        logger.debug("Toggle QQ window triggered (Enter key)")
        system_service.toggle_qq_window()

    def shutdown_computer(self):
        logger.warning("Shutdown computer requested!")
        system_service.shutdown_computer()

    def move_to_front(self):
        logger.debug("Move window to front")
        self.show()
        self.raise_()
        self.activateWindow()

    def exit_app(self):
        logger.info("Exiting application")
        keyboard_service.stop_listening()
        self.app.quit()

    def closeEvent(self, event):
        event.ignore()

    def on_tray_icon_activated(self, reason):
        logger.debug(f"Tray icon activated: reason={reason}")
        if reason == QSystemTrayIcon.Trigger:
            self.move_to_front()

    def show_context_menu(self, position):
        self.tray_menu.menu.exec_(self.countdown_label.mapToGlobal(position))

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.offset)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.toggle_qq_window()

    def event(self, event):
        if event.type() == QEvent.User:
            logger.info("Update available event received, prompting user")
            if ReminderDialog.show_update_available(self):
                self.update_application()
            return True
        return super().event(event)