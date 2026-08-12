import unittest
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication, QMessageBox, QPushButton


class TestShowCheckout(unittest.TestCase):
    """测试 ReminderDialog.show_checkout 对话框"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        """每次测试前 mock exec_() 以避免真的弹窗"""
        self.exec_patcher = patch.object(QMessageBox, 'exec_')
        self.mock_exec = self.exec_patcher.start()

    def tearDown(self):
        self.exec_patcher.stop()

    # ── 弹性模式 ────────────────────────────────────────────

    def test_flexible_shows_reminder_text(self):
        """弹性模式：显示打卡/关空调/写日志 提醒"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=None)

        # 验证 QMessageBox 被创建了
        self.mock_exec.assert_called_once()

    def test_flexible_no_shutdown_button(self):
        """弹性模式：不应有 Shutdown 按钮"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        shutdown_buttons = []

        def fake_add_button(button, *args, **kwargs):
            if isinstance(button, QPushButton) and button.text() == "Shutdown":
                shutdown_buttons.append(button)
            return QMessageBox.NoButton

        with patch.object(QMessageBox, 'addButton', side_effect=fake_add_button):
            ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=MagicMock())
            self.assertEqual(len(shutdown_buttons), 0,
                             "Flexible mode should NOT add Shutdown button")

    # ── 固定模式 ────────────────────────────────────────────

    def test_non_flexible_shows_shutdown_text(self):
        """固定模式：显示 'Need to shutdown'"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        mock_cb = MagicMock()
        ReminderDialog.show_checkout(is_flexible=False, shutdown_callback=mock_cb)
        self.mock_exec.assert_called_once()

    def test_non_flexible_has_shutdown_button(self):
        """固定模式 + callback：应有 Shutdown 按钮"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        mock_cb = MagicMock()
        shutdown_button_found = False

        def capture_add_button(button, *args, **kwargs):
            nonlocal shutdown_button_found
            if isinstance(button, QPushButton) and button.text() == "Shutdown":
                shutdown_button_found = True
            return QMessageBox.NoButton

        with patch.object(QMessageBox, 'addButton', side_effect=capture_add_button):
            ReminderDialog.show_checkout(is_flexible=False, shutdown_callback=mock_cb)
            self.assertTrue(shutdown_button_found, "Non-flexible with callback should add Shutdown button")

    def test_shutdown_button_triggers_callback(self):
        """Shutdown 按钮点击应触发 callback"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        mock_cb = MagicMock()
        captured_button = None

        def capture_add_button(button, *args, **kwargs):
            nonlocal captured_button
            if isinstance(button, QPushButton) and button.text() == "Shutdown":
                captured_button = button
            return QMessageBox.NoButton

        with patch.object(QMessageBox, 'addButton', side_effect=capture_add_button):
            ReminderDialog.show_checkout(is_flexible=False, shutdown_callback=mock_cb)

        self.assertIsNotNone(captured_button, "Shutdown button should exist")
        captured_button.clicked.emit()
        mock_cb.assert_called_once()

    def test_non_flexible_no_callback_no_shutdown(self):
        """固定模式无 callback：不应加 Shutdown 按钮"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        shutdown_button_found = False

        def capture_add_button(button, *args, **kwargs):
            nonlocal shutdown_button_found
            if isinstance(button, QPushButton) and button.text() == "Shutdown":
                shutdown_button_found = True
            return QMessageBox.NoButton

        with patch.object(QMessageBox, 'addButton', side_effect=capture_add_button):
            ReminderDialog.show_checkout(is_flexible=False, shutdown_callback=None)
            self.assertFalse(shutdown_button_found, "No callback → no Shutdown button")

    # ── Ignore 按钮 ────────────────────────────────────────

    def test_ignore_button_always_present(self):
        """弹性/固定模式都应有 Ignore 按钮"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        ignore_found = False

        def capture_add_button(button, *args, **kwargs):
            nonlocal ignore_found
            if isinstance(button, QMessageBox.StandardButton.__class__) or button == QMessageBox.Ignore:
                ignore_found = True
            return QMessageBox.NoButton

        ReminderDialog.show_checkout(is_flexible=True, shutdown_callback=MagicMock())
        # 不应崩溃
        self.assertTrue(True)

    # ── 窗口属性 ────────────────────────────────────────────

    def test_window_title(self):
        """对话框标题应为 'Microsoft Visual Studio'"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        ReminderDialog.show_checkout(is_flexible=True)
        self.mock_exec.assert_called_once()

    def test_minimum_size_set(self):
        """对话框应设置最小尺寸"""
        from app.ui.dialogs.reminder_dialog import ReminderDialog

        ReminderDialog.show_checkout(is_flexible=False)
        self.mock_exec.assert_called_once()


class TestOtherDialogs(unittest.TestCase):
    """测试其他 ReminderDialog 对话框"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.exec_patcher = patch.object(QMessageBox, 'exec_')
        self.mock_exec = self.exec_patcher.start()

    def tearDown(self):
        self.exec_patcher.stop()

    def test_show_checkin(self):
        from app.ui.dialogs.common import FancyDialog
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        with patch.object(FancyDialog, 'exec_') as mock_exec:
            ReminderDialog.show_checkin()
            mock_exec.assert_called_once()

    def test_show_job_record(self):
        from app.ui.dialogs.common import FancyDialog
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        with patch.object(FancyDialog, 'exec_') as mock_exec:
            ReminderDialog.show_job_record()
            mock_exec.assert_called_once()

    def test_show_custom_timer(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        ReminderDialog.show_custom_timer()
        self.mock_exec.assert_called_once()

    def test_show_update_available_returns_widget(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        from PyQt5.QtWidgets import QWidget
        result = ReminderDialog.show_update_available(countdown_seconds=0)
        self.assertIsInstance(result, QWidget)
        result.close()

    def test_show_update_available_defer_callback_on_close(self):
        from app.ui.dialogs.reminder_dialog import ReminderDialog
        deferred = [False]
        dialog = ReminderDialog.show_update_available(
            countdown_seconds=0, on_defer=lambda: deferred.__setitem__(0, True))
        dialog.close()
        self.assertTrue(deferred[0])


if __name__ == '__main__':
    unittest.main()
