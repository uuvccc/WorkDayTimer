import os
import random
import datetime
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QMessageBox, QApplication, QDialog, QSystemTrayIcon, QVBoxLayout

from app.config.constants import (
    ICON_FILE, IMAGE_DIRECTORY, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT
)
from app.config.manager import config_manager
from app.services import time_service, system_service, update_service, keyboard_service
from app.ui import TrayMenu, SettingsDialog, CustomTimerDialog, ReminderDialog, ascii_art
from app.utils.image import transparent_pixmap
from app.utils.logger import logger

class MainWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        logger.debug("MainWindow.__init__ start")
        self._setup_ui()
        self._setup_tray_menu()
        self._setup_timers()
        self._setup_keyboard_hook()
        self._schedule_auto_update_check()
        logger.info("MainWindow initialization complete")

    def _setup_ui(self):
        logger.debug("Setting up UI components")
        self.setFocusPolicy(Qt.StrongFocus)

        # 图片模式：随机轮换图片
        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("background: transparent;")
        self.countdown_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.countdown_label.customContextMenuRequested.connect(self.show_context_menu)

        # ASCII 模式：字符动画
        self.ascii_label = QLabel(self)
        self.ascii_label.setFont(QFont("Consolas", 10))
        self.ascii_label.setAlignment(Qt.AlignCenter)
        self.ascii_label.setWordWrap(False)
        self.ascii_label.setTextFormat(Qt.PlainText)
        self.ascii_label.setStyleSheet("background: transparent; color: #FFFFFF;")
        self.ascii_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ascii_label.customContextMenuRequested.connect(self.show_context_menu)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_timer_display)
        self.display_timer.start(100)
        logger.debug("Display timer started (100ms interval)")

        self.time_label = QLabel('', self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("background: transparent; color: rgba(255,255,255,0.85); font-size: 9px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(2)
        layout.addWidget(self.countdown_label, 1, Qt.AlignCenter)
        layout.addWidget(self.ascii_label, 1)
        layout.addWidget(self.time_label)

        self.setParent(None)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        screen_rect = QApplication.primaryScreen().availableGeometry()
        x = screen_rect.right() - WINDOW_SIZE_WIDTH - 10
        y = screen_rect.top() + 10
        self.setGeometry(x, y, WINDOW_SIZE_WIDTH, WINDOW_SIZE_HEIGHT)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()
        logger.debug(f"Window positioned at ({x}, {y}), size=({WINDOW_SIZE_WIDTH}x{WINDOW_SIZE_HEIGHT})")

        self._setup_ascii_animation()

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
            # 推迟到 __init__ 完成后弹出：show_checkin_reminder 内部是模态 exec_()，
            # 若在初始化中途调用会阻塞剩余初始化（如 tray_menu 尚未创建），
            # 导致右键图片时报 'MainWindow' object has no attribute 'tray_menu'。
            QTimer.singleShot(0, self.show_checkin_reminder)

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

    def _schedule_auto_update_check(self):
        """根据配置延迟调度自动更新检测"""
        if not config_manager.should_auto_check():
            logger.info("Auto update check is disabled or deferred, skipping")
            return
        delay_ms = config_manager.check_update_delay * 1000
        logger.info(f"Scheduling auto update check in {config_manager.check_update_delay}s")
        QTimer.singleShot(delay_ms, self._check_for_updates)

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

        display_text = '⏳ {:.0f}s'.format(seconds)
        if custom_timer_seconds > 0:
            display_text += '  ⏱️ {:.0f}s'.format(custom_timer_seconds)
        self.time_label.setText(display_text)
        self.time_label.adjustSize()

        # 每 60s 重新掷一次显示模式：一半概率图片 / 一半概率 ASCII 动画
        now = datetime.datetime.now()
        if getattr(self, '_last_mode_roll', None) is None:
            self._last_mode_roll = now
        elif (now - self._last_mode_roll).total_seconds() > 60:
            self._last_mode_roll = now
            self._roll_mode()

        # 按应用状态刷新 ASCII 场景（待机 / 自定义计时→时钟 / 快下班→犯困）
        self._refresh_ascii_scene()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.show()

    # ── ASCII 动画播放器 ───────────────────────────────────

    def _setup_ascii_animation(self):
        """初始化显示：随机选待机场景 + 掷一次显示模式（一半图片/一半 ASCII）。"""
        self._idle_scene = random.choice(ascii_art.IDLE_SCENES)
        self._scene_name = None
        self._frame_index = 0
        self._celebrating = False

        self._ascii_timer = QTimer(self)
        self._ascii_timer.timeout.connect(self._advance_ascii_frame)

        self._scene_timer = QTimer(self)
        self._scene_timer.timeout.connect(self._switch_idle_scene)
        self._scene_timer.start(20000)

        # 启动时掷一次显示模式：一半概率随机图片，一半概率 ASCII 动画
        self._display_mode = random.choice(['image', 'ascii'])
        logger.info(f"Display mode rolled: {self._display_mode}")
        self._apply_mode()

    def _switch_idle_scene(self):
        """每 20s 换一个待机形象（猫/兔/咖啡/打工人）。"""
        self._idle_scene = random.choice(ascii_art.IDLE_SCENES)

    def _advance_ascii_frame(self):
        scene = ascii_art.SCENES[self._scene_name]
        self._frame_index = (self._frame_index + 1) % len(scene["frames"])
        self.ascii_label.setText(ascii_art.render_frame(scene, self._frame_index))

    def _set_scene(self, name):
        """切换场景并重置播放（fps/颜色/文本格式跟着场景走）。"""
        if self._scene_name == name:
            return
        self._scene_name = name
        self._frame_index = 0
        scene = ascii_art.SCENES[name]
        if scene.get("rainbow"):
            self.ascii_label.setTextFormat(Qt.RichText)
            self.ascii_label.setStyleSheet("background: transparent;")
        else:
            self.ascii_label.setTextFormat(Qt.PlainText)
            self.ascii_label.setStyleSheet(
                "background: transparent; color: {};".format(scene["color"]))
        self._ascii_timer.setInterval(int(1000 / scene["fps"]))
        self._ascii_timer.start()
        self._advance_ascii_frame()

    def _ensure_ascii_running(self):
        """确保 ASCII 播放器在跑（从图片模式切回来时定时器可能已停）。"""
        if self._scene_name is None:
            self._set_scene(self._decide_scene())
        elif not self._ascii_timer.isActive():
            scene = ascii_art.SCENES[self._scene_name]
            self._ascii_timer.setInterval(int(1000 / scene["fps"]))
            self._ascii_timer.start()
            self._advance_ascii_frame()

    def _apply_mode(self):
        """按当前 _display_mode 显示：随机图片 或 ASCII 动画，二选一。"""
        if self._display_mode == 'ascii':
            self.ascii_label.show()
            self.countdown_label.hide()
            self._ensure_ascii_running()
        else:
            self.countdown_label.show()
            self.ascii_label.hide()
            self._ascii_timer.stop()
            self._pick_random_image()

    def _roll_mode(self):
        """每 60s 重新掷一次显示模式：一半概率图片 / 一半概率 ASCII。"""
        self._display_mode = random.choice(['image', 'ascii'])
        logger.info(f"Display mode re-rolled: {self._display_mode}")
        self._apply_mode()

    def _pick_random_image(self):
        """从 images/timers/ 随机选一张图显示（保留原有随机换图逻辑）。"""
        try:
            image_files = [
                f for f in os.listdir(IMAGE_DIRECTORY)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
        except OSError as e:
            logger.error(f"Failed to list image directory: {e}")
            image_files = []
        if not image_files:
            logger.warning("No pet images found, falling back to ASCII animation")
            self._display_mode = 'ascii'
            self._apply_mode()
            return
        image_path = os.path.join(IMAGE_DIRECTORY, random.choice(image_files))
        pixmap = transparent_pixmap(image_path).scaled(
            60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.countdown_label.setPixmap(pixmap)
        logger.debug(f"Picked pet image: {os.path.basename(image_path)}")

    def _refresh_ascii_scene(self):
        """按应用状态决定目标场景并切换（每 100ms 刷新，切场景很廉价）。

        仅 ASCII 模式生效；图片模式下不动动画（等 _roll_mode 掷回来）。
        """
        if not hasattr(self, '_display_mode') or self._display_mode != 'ascii':
            return
        target = self._decide_scene()
        self._set_scene(target)

    def _decide_scene(self):
        custom = getattr(self, 'custom_timer', None)
        if custom is not None and custom.isActive():
            return 'clock'
        if self._celebrating:
            return 'celebrate'
        rem = getattr(self, 'reminder_timer', None)
        if rem is not None and rem.isActive() and rem.remainingTime() < 10 * 60 * 1000:
            return 'sleepy'
        return self._idle_scene

    def _celebrate_once(self):
        """完工/倒计时结束：切到 ASCII 庆祝动画播几秒，再回待机。"""
        self._celebrating = True
        self._display_mode = 'ascii'
        self._apply_mode()
        self._refresh_ascii_scene()
        QTimer.singleShot(4000, self._stop_celebrate)

    def _stop_celebrate(self):
        self._celebrating = False

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
        self._celebrate_once()

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
        if not hasattr(self, 'tray_menu'):
            logger.warning("Context menu requested before tray menu is initialized")
            return
        self.tray_menu.menu.exec_(self.sender().mapToGlobal(position))

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
            logger.info("Update available event received, showing non-modal dialog")
            ReminderDialog.show_update_available(
                parent=self,
                countdown_seconds=config_manager.check_update_delay,
                on_update=self._on_update_now,
                on_defer=self._on_defer_update,
                on_disable=self._on_disable_update,
            )
            return True
        return super().event(event)

    def _on_update_now(self):
        """用户选择立即更新"""
        logger.info("User chose: update now")
        config_manager.clear_defer()
        self.update_application()

    def _on_defer_update(self):
        """用户选择下次提醒，7 天内不再自动检测"""
        logger.info("User chose: defer update")
        config_manager.defer_update()

    def _on_disable_update(self):
        """用户选择不再提示，关闭自动检测"""
        logger.info("User chose: disable auto update")
        config_manager.auto_check_update = False