from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QMessageBox,
    QListWidget, QListWidgetItem, QStackedWidget, QWidget,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import threading
from app.config.manager import config_manager
from app.services import system_service, update_service
from app.ui.dialogs.common import center_on_screen, is_card_style
from app.utils.logger import logger

# 卡片风格下的侧边栏样式（Windows 风格用原生外观）
SIDEBAR_STYLE = """
QListWidget {
    background: #f5f5f5;
    border: none;
    border-right: 1px solid #e0e0e0;
    padding: 6px 0;
    outline: none;
}
QListWidget::item {
    padding: 10px 16px;
    border: none;
    color: #444;
    font-size: 13px;
}
QListWidget::item:hover {
    background: #e8e8e8;
}
QListWidget::item:selected {
    background: #e0e0e0;
    color: #111;
    font-weight: bold;
}
"""

DIALOG_STYLES = [
    ("windows", "Windows (native)"),
    ("card", "Card (colorful)"),
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None, update_callback=None, apply_callback=None):
        super().__init__(parent)
        self._update_callback = update_callback
        # 点 OK 保存后回调（父窗口用来即时重连输入反馈 Hook 等运行态设置）
        self._apply_callback = apply_callback
        logger.debug("SettingsDialog opening")
        self.setWindowTitle("Settings")
        # 卡片风格用 Tool 小窗，Windows 风格用原生对话框标题栏
        flags = Qt.Tool if is_card_style() else Qt.Dialog
        self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(520, 340)
        self.resize(520, 360)
        self._build_ui()
        self._connect_signals()
        self.sidebar.setCurrentRow(0)
        self._load_settings()
        center_on_screen(self)

    # ── Layout ────────────────────────────────────────────

    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Sidebar ──
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        if is_card_style():
            self.sidebar.setStyleSheet(SIDEBAR_STYLE)
        self.sidebar.setFocusPolicy(Qt.NoFocus)

        self._add_nav_item("General", 0)
        self._add_nav_item("Pet", 1)
        self._add_nav_item("Reminders", 2)
        self._add_nav_item("System", 3)
        self._add_nav_item("About", 4)

        outer.addWidget(self.sidebar)

        # ── Content ──
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(24, 20, 24, 12)
        right_panel.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_general())
        self.stack.addWidget(self._page_pet())
        self.stack.addWidget(self._page_reminders())
        self.stack.addWidget(self._page_system())
        self.stack.addWidget(self._page_about())

        right_panel.addWidget(self.stack, 1)

        # ── Bottom Bar ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        if is_card_style():
            sep.setStyleSheet("color: #e0e0e0;")
        right_panel.addWidget(sep)
        right_panel.addSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        right_panel.addLayout(btn_row)

        right_cont = QWidget()
        right_cont.setLayout(right_panel)
        outer.addWidget(right_cont, 1)

        if is_card_style():
            self.setStyleSheet("QDialog { background: #fafafa; }")

    def _add_nav_item(self, text, idx):
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, idx)
        self.sidebar.addItem(item)

    def _connect_signals(self):
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

    # ── Page: General ─────────────────────────────────────

    def _page_general(self):
        page = self._page_wrapper("Work Mode")

        self.flexible_checkbox = QCheckBox("Use flexible work hours")
        page.layout().addWidget(self.flexible_checkbox)

        # ── Work hours ──
        wh_label = QLabel("Daily work hours:")
        wh_label.setStyleSheet("color: #555; margin-top: 8px;")
        self.work_hours_spin = QDoubleSpinBox()
        self.work_hours_spin.setRange(1.0, 24.0)
        self.work_hours_spin.setSingleStep(0.5)
        self.work_hours_spin.setDecimals(1)
        self.work_hours_spin.setSuffix(" h")
        self.work_hours_spin.setFixedWidth(100)
        wh_row = QHBoxLayout()
        wh_row.addWidget(wh_label)
        wh_row.addWidget(self.work_hours_spin)
        wh_row.addStretch()
        page.layout().addLayout(wh_row)

        # ── Fixed start time ──
        fs_label = QLabel("Fixed-mode start time:")
        fs_label.setStyleSheet("color: #555; margin-top: 4px;")
        self.fixed_start_spin = QDoubleSpinBox()
        self.fixed_start_spin.setRange(0.0, 23.5)
        self.fixed_start_spin.setSingleStep(0.5)
        self.fixed_start_spin.setDecimals(1)
        self.fixed_start_spin.setSuffix(":00")
        self.fixed_start_spin.setFixedWidth(100)
        fs_row = QHBoxLayout()
        fs_row.addWidget(fs_label)
        fs_row.addWidget(self.fixed_start_spin)
        fs_row.addStretch()
        page.layout().addLayout(fs_row)

        # ── Job record reminder offset ──
        jr_label = QLabel("Job log reminder before end:")
        jr_label.setStyleSheet("color: #555; margin-top: 4px;")
        self.job_record_spin = QSpinBox()
        self.job_record_spin.setRange(0, 480)
        self.job_record_spin.setSingleStep(5)
        self.job_record_spin.setSuffix(" min")
        self.job_record_spin.setFixedWidth(100)
        jr_row = QHBoxLayout()
        jr_row.addWidget(jr_label)
        jr_row.addWidget(self.job_record_spin)
        jr_row.addStretch()
        page.layout().addLayout(jr_row)

        # ── Dialog style ──
        ds_label = QLabel("Dialog style:")
        ds_label.setStyleSheet("color: #555; margin-top: 4px;")
        self.dialog_style_combo = QComboBox()
        for value, text in DIALOG_STYLES:
            self.dialog_style_combo.addItem(text, value)
        self.dialog_style_combo.setFixedWidth(160)
        ds_row = QHBoxLayout()
        ds_row.addWidget(ds_label)
        ds_row.addWidget(self.dialog_style_combo)
        ds_row.addStretch()
        page.layout().addLayout(ds_row)

        ds_note = QLabel("Applies to dialogs opened after this setting is saved.")
        ds_note.setWordWrap(True)
        ds_note.setStyleSheet("color: #888; margin-top: 2px;")
        page.layout().addWidget(ds_note)

        page.layout().addStretch()
        return page

    # ── Page: Pet ─────────────────────────────────────────

    def _page_pet(self):
        page = self._page_wrapper("Pet Display")

        self.input_feedback_checkbox = QCheckBox(
            "Show key & mouse feedback bubble")
        page.layout().addWidget(self.input_feedback_checkbox)

        desc = QLabel(
            "Shows every key you press and every mouse button you click "
            "as an ASCII bubble above the pet (stream-style key display).\n"
            "Note: this shows typed text on screen, including passwords.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-top: 4px;")
        page.layout().addWidget(desc)

        page.layout().addStretch()
        return page

    # ── Page: Reminders ───────────────────────────────────

    def _page_reminders(self):
        page = self._page_wrapper("Reminders")
        self.checkin_checkbox = QCheckBox("Show check-in notification at startup")
        self.job_record_checkbox = QCheckBox("Remind me to log work before the day ends")
        self.checkout_checkbox = QCheckBox("Show check-out reminder at work end")
        page.layout().addWidget(self.checkin_checkbox)
        page.layout().addWidget(self.job_record_checkbox)
        page.layout().addWidget(self.checkout_checkbox)
        page.layout().addStretch()
        return page

    # ── Page: System ──────────────────────────────────────

    def _page_system(self):
        page = self._page_wrapper("System")
        self.startup_checkbox = QCheckBox("Start MiniTools automatically when you log in")
        desc = QLabel("Adds an entry to the Windows startup registry for the current user.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-top: 4px;")
        page.layout().addWidget(self.startup_checkbox)
        page.layout().addWidget(desc)

        page.layout().addSpacing(12)

        # ── Auto check update ──
        self.auto_update_checkbox = QCheckBox("Automatically check for updates on startup")
        page.layout().addWidget(self.auto_update_checkbox)

        delay_row = QHBoxLayout()
        delay_label = QLabel("Delay before checking:")
        delay_label.setStyleSheet("color: #555; margin-top: 4px;")
        self.update_delay_spin = QSpinBox()
        self.update_delay_spin.setRange(0, 300)
        self.update_delay_spin.setSingleStep(5)
        self.update_delay_spin.setSuffix(" s")
        self.update_delay_spin.setFixedWidth(100)
        delay_row.addWidget(delay_label)
        delay_row.addWidget(self.update_delay_spin)
        delay_row.addStretch()
        page.layout().addLayout(delay_row)

        page.layout().addStretch()
        return page

    # ── Page: About ───────────────────────────────────────

    def _page_about(self):
        page = self._page_wrapper("About")
        layout = page.layout()

        version = update_service.get_current_version()
        name = QLabel(f"MiniTools  v{version}" if version else "MiniTools")
        name.setFont(QFont(page.font().family(), 13, QFont.Bold))
        layout.addWidget(name)

        desc = QLabel("A lightweight workday countdown & reminder utility.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-top: 6px;")
        layout.addWidget(desc)

        layout.addSpacing(12)

        shortcut = QLabel("<b>Enter</b> — Toggle QQ window visibility")
        shortcut.setStyleSheet("color: #555;")
        layout.addWidget(shortcut)

        layout.addSpacing(20)

        self.check_update_btn = QPushButton("Check for Updates...")
        self.check_update_btn.clicked.connect(self._on_check_updates)
        self.check_update_btn.setFixedWidth(180)
        layout.addWidget(self.check_update_btn)

        layout.addStretch()
        return page

    @staticmethod
    def _page_wrapper(title_text):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        title = QLabel(title_text)
        title.setFont(QFont(page.font().family(), 11, QFont.Bold))
        title.setStyleSheet("color: #222; padding-bottom: 6px;")
        layout.addWidget(title)
        return page

    # ── Read / Write ──────────────────────────────────────

    def _load_settings(self):
        logger.debug("Loading settings into dialog controls")
        self.flexible_checkbox.setChecked(config_manager.is_flexible)
        self.work_hours_spin.setValue(config_manager.work_hours)
        self.fixed_start_spin.setValue(config_manager.fixed_start_hour)
        self.job_record_spin.setValue(config_manager.job_record_before_end_minutes)
        self.checkin_checkbox.setChecked(config_manager.get_reminder_setting("checkin_reminder"))
        self.job_record_checkbox.setChecked(config_manager.get_reminder_setting("job_record_reminder"))
        self.checkout_checkbox.setChecked(config_manager.get_reminder_setting("checkout_reminder"))
        self.startup_checkbox.setChecked(system_service.is_run_on_startup())
        self.auto_update_checkbox.setChecked(config_manager.auto_check_update)
        self.update_delay_spin.setValue(config_manager.check_update_delay)
        self.input_feedback_checkbox.setChecked(config_manager.show_input_feedback)
        idx = self.dialog_style_combo.findData(config_manager.dialog_style)
        self.dialog_style_combo.setCurrentIndex(max(idx, 0))

    def _on_ok(self):
        logger.debug("Settings OK button clicked")
        old_flexible = config_manager.is_flexible
        new_flexible = self.flexible_checkbox.isChecked()
        config_manager.is_flexible = new_flexible

        config_manager.auto_check_update = self.auto_update_checkbox.isChecked()
        config_manager.check_update_delay = self.update_delay_spin.value()

        config_manager.work_hours = self.work_hours_spin.value()
        config_manager.fixed_start_hour = self.fixed_start_spin.value()
        config_manager.job_record_before_end_minutes = self.job_record_spin.value()

        config_manager.set_reminder_setting("checkin_reminder", self.checkin_checkbox.isChecked())
        config_manager.set_reminder_setting("job_record_reminder", self.job_record_checkbox.isChecked())
        config_manager.set_reminder_setting("checkout_reminder", self.checkout_checkbox.isChecked())

        new_startup = self.startup_checkbox.isChecked()
        success, msg = system_service.toggle_run_on_startup(new_startup)
        if not success:
            logger.error(f"Failed to toggle startup: {msg}")
            QMessageBox.critical(self, "Error", msg)
            self.startup_checkbox.setChecked(not new_startup)
            return

        config_manager.show_input_feedback = self.input_feedback_checkbox.isChecked()
        config_manager.dialog_style = self.dialog_style_combo.currentData()

        self.accept()
        logger.info("Settings dialog accepted")

        # 运行态设置即时生效（输入反馈 Hook 重连等）
        if self._apply_callback:
            try:
                self._apply_callback()
            except Exception as e:
                logger.error(f"Apply callback failed: {e}", exc_info=True)

        if old_flexible != new_flexible:
            QMessageBox.information(
                self, "Mode Changed",
                "Flexible mode has been " + ("enabled." if new_flexible else "disabled.") + "\n"
                "Please restart the application for the change to take effect.",
            )

    def _on_check_updates(self):
        """手动检查更新。

        手动检查只做一次即时查询，与「启动时自动检测」开关（auto_check_update）
        无关——那个开关只控制启动时的后台自动检测，不应限制用户主动更新。
        """
        logger.debug("Check for updates button clicked (manual)")
        if getattr(self, "_checking_updates", False):
            return
        self._checking_updates = True
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("Checking...")

        self._check_update_result = None
        threading.Thread(target=self._do_check_updates, daemon=True).start()

        # 用挂在对话框上的定时器轮询后台线程结果：对话框销毁时定时器随之销毁，
        # 不会在窗口关闭后回调到已释放的对象。
        self._check_timer = QTimer(self)
        self._check_timer.setInterval(100)
        self._check_timer.timeout.connect(self._poll_check_update_result)
        self._check_timer.start()

    def _do_check_updates(self):
        try:
            self._check_update_result = update_service.check_for_updates()
        except Exception as e:
            logger.error(f"Manual update check failed: {e}", exc_info=True)
            self._check_update_result = (False, None, None)

    def _poll_check_update_result(self):
        if self._check_update_result is None:
            return
        self._check_timer.stop()

        has_update, latest_version, current_version = self._check_update_result
        self._checking_updates = False
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("Check for Updates...")

        if has_update:
            logger.info(f"Manual check found update: {latest_version}")
            reply = QMessageBox.question(
                self, "Update Available",
                f"A new version v{latest_version} is available "
                f"(current v{current_version}).\n\nUpdate now?")
            if reply == QMessageBox.Yes and self._update_callback:
                self._update_callback()
        elif current_version is None:
            QMessageBox.warning(self, "Update Check Failed",
                                "Could not determine the current version.")
        elif latest_version:
            logger.info("Manual check: already up to date")
            QMessageBox.information(
                self, "No Updates",
                f"You are already using the latest version (v{current_version}).")
        else:
            QMessageBox.warning(
                self, "Update Check Failed",
                "Could not check for updates.\n"
                "Please check your network connection and try again.")
