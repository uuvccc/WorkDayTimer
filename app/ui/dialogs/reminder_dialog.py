from PyQt5.QtWidgets import (QMessageBox, QPushButton, QWidget, QApplication,
                              QVBoxLayout, QLabel, QHBoxLayout)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
from app.utils.logger import logger

class ReminderDialog:
    @staticmethod
    def show_checkin(parent=None):
        logger.debug("Showing check-in reminder dialog")
        dialog = QMessageBox(parent)
        # 必须保留 Qt.Dialog 窗口类型位：否则 setWindowFlags 会把类型掩码当作
        # Qt.Widget，QMessageBox 从顶层对话框降级成父窗口的内嵌子控件，
        # 被 200x200 的宠物窗口裁剪掉，表现为"弹不出来"。
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
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
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dialog.setWindowTitle("Work Record Reminder")
        dialog.setText("Please remember to record your work progress!")
        dialog.setIcon(QMessageBox.Information)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec_()

    @staticmethod
    def show_checkout(parent=None, is_flexible=True, shutdown_callback=None):
        logger.debug(f"Showing checkout reminder dialog: is_flexible={is_flexible}, has_shutdown_cb={shutdown_callback is not None}")
        dialog = QMessageBox(parent)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
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
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dialog.setWindowTitle("Custom Timer")
        dialog.setText("Custom timer countdown finished!")
        dialog.setIcon(QMessageBox.Information)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec_()

    @staticmethod
    def show_update_available(parent=None, countdown_seconds=10,
                              on_update=None, on_defer=None, on_disable=None):
        """非模态更新提示弹窗，带倒计时。
        - on_update: 点击“立即更新”
        - on_defer:  点击“下次提醒”或关闭弹窗
        - on_disable: 点击“不再提示”
        """
        logger.debug("Showing update available dialog (non-modal, QWidget)")

        dialog = QWidget()
        dialog.setAttribute(Qt.WA_DeleteOnClose)
        dialog.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        dialog.setWindowTitle("Update Available")
        dialog.resize(420, 220)

        # 居中屏幕
        screen = QApplication.primaryScreen().availableGeometry()
        dialog.move(
            (screen.width() - dialog.width()) // 2,
            (screen.height() - dialog.height()) // 2,
        )

        font = QFont()
        font.setPointSize(12)
        dialog.setFont(font)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(12)

        title = QLabel("Update Available")
        title.setFont(QFont(dialog.font().family(), 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        msg = QLabel("A new version of MiniTools is available!\n"
                     "Do you want to update now?")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #444;")
        layout.addWidget(msg)

        layout.addStretch()

        # ── 按钮行 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        update_btn = QPushButton(f"Update Now ({countdown_seconds}s)")
        update_btn.setFixedHeight(34)
        update_btn.setEnabled(False)
        update_btn.setStyleSheet(
            "QPushButton { background: #4CAF50; color: white; border: none; "
            "border-radius: 4px; padding: 6px 16px; }"
            "QPushButton:disabled { background: #ccc; color: #888; }"
            "QPushButton:hover:!disabled { background: #45a049; }"
        )

        defer_btn = QPushButton("Remind Later")
        defer_btn.setFixedHeight(34)
        defer_btn.setStyleSheet(
            "QPushButton { background: #f5f5f5; color: #333; border: 1px solid #ddd; "
            "border-radius: 4px; padding: 6px 16px; }"
            "QPushButton:hover { background: #e8e8e8; }"
        )

        disable_btn = QPushButton("Don't Remind")
        disable_btn.setFixedHeight(34)
        disable_btn.setStyleSheet(
            "QPushButton { background: #f5f5f5; color: #999; border: 1px solid #ddd; "
            "border-radius: 4px; padding: 6px 16px; }"
            "QPushButton:hover { background: #e8e8e8; }"
        )

        btn_row.addWidget(disable_btn)
        btn_row.addStretch()
        btn_row.addWidget(defer_btn)
        btn_row.addWidget(update_btn)
        layout.addLayout(btn_row)

        # ── 倒计时（从 0 开始数到 countdown_seconds）──
        elapsed = [0]

        def tick():
            elapsed[0] += 1
            if elapsed[0] < countdown_seconds:
                update_btn.setText(f"Update Now ({elapsed[0]}s)")
            else:
                update_btn.setText("Update Now")
                update_btn.setEnabled(True)
                timer.stop()

        timer = QTimer(dialog)
        timer.timeout.connect(tick)
        timer.start(1000)

        # ── 回调 ──
        handled = [False]

        def do_update():
            if handled[0]:
                return
            handled[0] = True
            timer.stop()
            dialog.close()
            logger.info("User chose: update now")
            if on_update:
                on_update()

        def do_defer():
            if handled[0]:
                return
            handled[0] = True
            timer.stop()
            dialog.close()
            logger.info("User chose: remind later")
            if on_defer:
                on_defer()

        def do_disable():
            if handled[0]:
                return
            handled[0] = True
            timer.stop()
            dialog.close()
            logger.info("User chose: don't remind")
            if on_disable:
                on_disable()

        update_btn.clicked.connect(do_update)
        defer_btn.clicked.connect(do_defer)
        disable_btn.clicked.connect(do_disable)

        def on_close_event(event):
            if not handled[0]:
                handled[0] = True
                timer.stop()
                logger.info("Update dialog closed without action, treating as defer")
                if on_defer:
                    on_defer()
            event.accept()

        dialog.closeEvent = on_close_event
        dialog.show()
        return dialog