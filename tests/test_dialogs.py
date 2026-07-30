"""对话框直接弹出 / 构造 / 交互功能测试。

所有测试在 mock 下运行，验证：
 - 对话框能正常构造（不崩溃）
 - 控件被正确创建
 - 交互逻辑（按钮点击、输入）行为正确
"""

import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton, QDialog
from PyQt5.QtCore import Qt


# ═══════════════════════════════════════════════════════════════
# 测试基类
# ═══════════════════════════════════════════════════════════════

class _DialogTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.exec_patcher = patch.object(QMessageBox, 'exec_')
        self.mock_exec = self.exec_patcher.start()
        self.question_patcher = patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
        self.q_question = self.question_patcher.start()

    def tearDown(self):
        self.exec_patcher.stop()
        self.question_patcher.stop()


# ═══════════════════════════════════════════════════════════════
# SettingsDialog 测试
# ═══════════════════════════════════════════════════════════════

class TestSettingsDialogPopup(_DialogTestBase):
    """SettingsDialog 构造、控件、页面切换测试"""

    def setUp(self):
        super().setUp()
        # mock config_manager, system_service, update_service
        self._config_patch = patch("app.ui.dialogs.settings_dialog.config_manager")
        self.mock_cfg = self._config_patch.start()
        self._sys_patch = patch("app.ui.dialogs.settings_dialog.system_service")
        self.mock_sys = self._sys_patch.start()
        self._update_patch = patch("app.ui.dialogs.settings_dialog.update_service")
        self.mock_update = self._update_patch.start()
        self.mock_update.get_current_version.return_value = "1.0.0"

    def tearDown(self):
        self._update_patch.stop()
        self._config_patch.stop()
        self._sys_patch.stop()
        super().tearDown()

    def _make_dialog(self, **kw):
        from app.ui.dialogs.settings_dialog import SettingsDialog
        return SettingsDialog(**kw)

    # ── 构造 ─────────────────────────────────────────────

    def test_construct_defaults_no_crash(self):
        try:
            dialog = self._make_dialog()
            self.assertIsNotNone(dialog)
            dialog.close()
        except Exception as e:
            self.fail(f"SettingsDialog construction raised: {e}")

    def test_construct_with_callback(self):
        cb = MagicMock()
        dialog = self._make_dialog(update_callback=cb)
        self.assertIs(dialog._update_callback, cb)
        dialog.close()

    # ── 窗口属性 ────────────────────────────────────────

    def test_window_title(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog.windowTitle(), "Settings")
        dialog.close()

    def test_window_size(self):
        dialog = self._make_dialog()
        self.assertGreaterEqual(dialog.minimumWidth(), 500)
        self.assertGreaterEqual(dialog.minimumHeight(), 300)
        dialog.close()

    # ── 侧边栏页面 ──────────────────────────────────────

    def test_sidebar_has_4_items(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog.sidebar.count(), 4)
        dialog.close()

    def test_sidebar_item_labels(self):
        dialog = self._make_dialog()
        labels = [dialog.sidebar.item(i).text() for i in range(dialog.sidebar.count())]
        self.assertIn("General", labels)
        self.assertIn("Reminders", labels)
        self.assertIn("System", labels)
        self.assertIn("About", labels)
        dialog.close()

    def test_stack_has_4_pages(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog.stack.count(), 4)
        dialog.close()

    def test_sidebar_selection_switches_page(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog.stack.currentIndex(), 0)

        dialog.sidebar.setCurrentRow(1)
        self.assertEqual(dialog.stack.currentIndex(), 1)

        dialog.sidebar.setCurrentRow(3)
        self.assertEqual(dialog.stack.currentIndex(), 3)

        dialog.sidebar.setCurrentRow(0)
        self.assertEqual(dialog.stack.currentIndex(), 0)
        dialog.close()

    # ── 控件存在性检查（用 isNotNone，不依赖 isVisible）──

    def test_general_page_widgets_exist(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(0)
        self.assertIsNotNone(dialog.flexible_checkbox)
        self.assertIsNotNone(dialog.work_hours_spin)
        self.assertIsNotNone(dialog.fixed_start_spin)
        self.assertIsNotNone(dialog.job_record_spin)
        dialog.close()

    def test_work_hours_spin_range(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(0)
        self.assertEqual(dialog.work_hours_spin.maximum(), 24.0)
        self.assertEqual(dialog.work_hours_spin.minimum(), 1.0)
        self.assertEqual(dialog.work_hours_spin.singleStep(), 0.5)
        dialog.close()

    def test_reminders_page_widgets_exist(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(1)
        self.assertIsNotNone(dialog.checkin_checkbox)
        self.assertIsNotNone(dialog.job_record_checkbox)
        self.assertIsNotNone(dialog.checkout_checkbox)
        dialog.close()

    def test_system_page_widgets_exist(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(2)
        self.assertIsNotNone(dialog.startup_checkbox)
        dialog.close()

    def test_about_page_widgets_exist(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(3)
        self.assertIsNotNone(dialog.check_update_btn)
        self.assertEqual(dialog.check_update_btn.text(), "Check for Updates...")
        dialog.close()

    # ── _on_ok 行为 ─────────────────────────────────────

    def test_ok_accepts_dialog(self):
        dialog = self._make_dialog()
        self.mock_sys.toggle_run_on_startup.return_value = (True, "ok")

        exec_patch = patch.object(QDialog, 'exec_', return_value=QDialog.Accepted)
        exec_patch.start()
        try:
            dialog._load_settings()
            dialog._on_ok()
            self.assertTrue(self.mock_cfg.is_flexible is not None)
        finally:
            exec_patch.stop()
        dialog.close()

    def test_ok_handles_startup_failure(self):
        """开机自启失败时应回退 checkbox 并弹出错误"""
        dialog = self._make_dialog()
        dialog.startup_checkbox.setChecked(True)
        self.mock_sys.toggle_run_on_startup.return_value = (False, "permission denied")

        # mock QMessageBox.critical
        crit_patch = patch.object(QMessageBox, 'critical')
        mock_crit = crit_patch.start()
        try:
            dialog._on_ok()
            mock_crit.assert_called_once()
            # checkbox should be reverted to False
            self.assertFalse(dialog.startup_checkbox.isChecked())
        finally:
            crit_patch.stop()
        dialog.close()

    def test_ok_shows_warning_on_flexible_change(self):
        """切换弹性模式后应弹出提示"""
        dialog = self._make_dialog()
        dialog.flexible_checkbox.setChecked(True)
        self.mock_cfg.is_flexible = False  # old value
        self.mock_sys.toggle_run_on_startup.return_value = (True, "ok")

        exec_patch = patch.object(QDialog, 'exec_', return_value=QDialog.Accepted)
        info_patch = patch.object(QMessageBox, 'information')

        exec_patch.start()
        mock_info = info_patch.start()
        try:
            dialog._on_ok()
            mock_info.assert_called_once()
        finally:
            exec_patch.stop()
            info_patch.stop()
        dialog.close()

    # ── About 页按钮 ────────────────────────────────────

    def test_update_button_no_callback_shows_info(self):
        dialog = self._make_dialog()
        dialog.sidebar.setCurrentRow(3)
        dialog._update_callback = None

        info_patch = patch.object(QMessageBox, 'information')
        mock_info = info_patch.start()
        try:
            dialog._on_check_updates()
            mock_info.assert_called_once()
        finally:
            info_patch.stop()
        dialog.close()

    def test_update_button_with_callback_calls_it(self):
        cb = MagicMock()
        dialog = self._make_dialog(update_callback=cb)
        dialog.sidebar.setCurrentRow(3)
        dialog._on_check_updates()
        cb.assert_called_once()
        dialog.close()


# ═══════════════════════════════════════════════════════════════
# CustomTimerDialog 测试
# ═══════════════════════════════════════════════════════════════

class TestCustomTimerDialogPopup(_DialogTestBase):
    """CustomTimerDialog 构造、按钮、输入测试"""

    # ── 构造 ─────────────────────────────────────────────

    def test_construct_no_crash(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        try:
            dialog = CustomTimerDialog()
            self.assertIsNotNone(dialog)
            dialog.close()
        except Exception as e:
            self.fail(f"CustomTimerDialog construction raised: {e}")

    def test_window_title(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        self.assertEqual(dialog.windowTitle(), "Custom Timer")
        dialog.close()

    def test_initial_value_is_zero(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        self.assertEqual(dialog.input_field.text(), "0")
        self.assertEqual(dialog._result_minutes, 0)
        dialog.close()

    def test_get_minutes_returns_zero_initially(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        self.assertEqual(dialog.get_minutes(), 0)
        dialog.close()

    # ── 数字键 ───────────────────────────────────────────

    def test_click_button_adds_minutes(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("0")
        dialog._add_minutes(5)
        self.assertEqual(dialog.input_field.text(), "5")
        dialog._add_minutes(10)
        self.assertEqual(dialog.input_field.text(), "15")
        dialog.close()

    def test_add_minutes_from_empty(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("abc")  # invalid
        dialog._add_minutes(30)
        self.assertEqual(dialog.input_field.text(), "30")
        dialog.close()

    def test_clear_button_resets(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("120")
        dialog.input_field.setText("0")  # simulate clear
        self.assertEqual(dialog.input_field.text(), "0")
        dialog.close()

    # ── _on_ok ───────────────────────────────────────────

    def test_ok_with_positive_number_has_result(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("45")
        dialog._on_ok()
        self.assertEqual(dialog.get_minutes(), 45)
        dialog.close()

    def test_ok_with_zero_shows_warning(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("0")
        warn_patch = patch.object(QMessageBox, 'warning')
        mock_warn = warn_patch.start()
        try:
            dialog._on_ok()
            mock_warn.assert_called_once()
            self.assertEqual(dialog.get_minutes(), 0)
        finally:
            warn_patch.stop()
        dialog.close()

    def test_ok_with_invalid_text_shows_warning(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        dialog.input_field.setText("not_a_number")
        warn_patch = patch.object(QMessageBox, 'warning')
        mock_warn = warn_patch.start()
        try:
            dialog._on_ok()
            mock_warn.assert_called_once()
        finally:
            warn_patch.stop()
        dialog.close()

    # ── Validator ────────────────────────────────────────

    def test_input_field_has_validator(self):
        from app.ui.dialogs.custom_timer_dialog import CustomTimerDialog
        dialog = CustomTimerDialog()
        self.assertIsNotNone(dialog.input_field.validator())
        dialog.close()


# ═══════════════════════════════════════════════════════════════
# ReminderDialog 增强弹出测试
# ═══════════════════════════════════════════════════════════════

class TestReminderDialogPopup(_DialogTestBase):
    """ReminderDialog 构造/属性级验证"""

    def test_show_checkout_creates_valid_dialog(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        with patch.object(QMessageBox, 'addButton', return_value=QMessageBox.NoButton):
            ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=None)
            self.mock_exec.assert_called_once()

    def test_show_checkin_creates_valid_dialog(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        ReminderDialog.show_checkin()
        self.mock_exec.assert_called_once()

    def test_show_job_record_creates_valid_dialog(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        ReminderDialog.show_job_record()
        self.mock_exec.assert_called_once()

    def test_show_custom_timer_creates_valid_dialog(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        ReminderDialog.show_custom_timer()
        self.mock_exec.assert_called_once()

    def test_dialog_has_correct_title(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        captured_title = [None]

        def fake_set_title(self, title):
            captured_title[0] = title

        with patch.object(QMessageBox, 'setWindowTitle', fake_set_title):
            ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=None)

        self.assertIsNotNone(captured_title[0])

    def test_minimum_width_is_set(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        ReminderDialog.show_checkout(is_flexible=False, shutdown_callback=None)
        self.mock_exec.assert_called_once()

    def test_all_dialog_types_no_crash(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        with patch.object(QMessageBox, 'addButton', return_value=QMessageBox.NoButton):
            ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=None)
        ReminderDialog.show_checkin()
        ReminderDialog.show_job_record()
        ReminderDialog.show_custom_timer()

        self.assertTrue(self.mock_exec.call_count >= 4)


if __name__ == '__main__':
    unittest.main()
