import unittest
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication, QPushButton

from app.ui.dialogs.common import LightDialog
from app.ui.dialogs.reminder_dialog import ReminderDialog


class TestShowCheckout(unittest.TestCase):
    """测试 ReminderDialog.show_checkout 对话框（浅色非模态版）"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _show_and_get_dialog(self, **kwargs):
        """patch show_centered 后调用 show_checkout，返回实际创建的对话框。"""
        with patch.object(LightDialog, 'show_centered') as mock_show:
            dialog = ReminderDialog.show_checkout(**kwargs)
            mock_show.assert_called_once()
            return dialog

    def _button_texts(self, dialog):
        texts = []
        for i in range(dialog.button_layout.count()):
            w = dialog.button_layout.itemAt(i).widget()
            if isinstance(w, QPushButton):
                texts.append(w.text())
        return texts

    def _find_button(self, dialog, text):
        for i in range(dialog.button_layout.count()):
            w = dialog.button_layout.itemAt(i).widget()
            if isinstance(w, QPushButton) and w.text() == text:
                return w
        return None

    # ── 弹性模式 ────────────────────────────────────────────

    def test_flexible_shows_reminder_text(self):
        """弹性模式：显示打卡/关空调/写日志 提醒"""
        dialog = self._show_and_get_dialog(is_flexible=True, shutdown_callback=None)
        self.assertIn("Clock out", dialog._detail_label.text())
        self.assertIn("Turn off AC", dialog._detail_label.text())

    def test_flexible_no_shutdown_button(self):
        """弹性模式：不应有 Shutdown 按钮"""
        dialog = self._show_and_get_dialog(is_flexible=True, shutdown_callback=MagicMock())
        self.assertNotIn("Shutdown", self._button_texts(dialog))

    # ── 固定模式 ────────────────────────────────────────────

    def test_non_flexible_shows_shutdown_text(self):
        """固定模式：显示 'Need to shutdown'"""
        dialog = self._show_and_get_dialog(is_flexible=False, shutdown_callback=MagicMock())
        self.assertIn("Need to shutdown", dialog._detail_label.text())

    def test_non_flexible_has_shutdown_button(self):
        """固定模式 + callback：应有 Shutdown 按钮"""
        dialog = self._show_and_get_dialog(is_flexible=False, shutdown_callback=MagicMock())
        self.assertIsNotNone(self._find_button(dialog, "Shutdown"),
                             "Non-flexible with callback should add Shutdown button")

    def test_shutdown_button_triggers_callback(self):
        """Shutdown 按钮点击应触发 callback"""
        mock_cb = MagicMock()
        dialog = self._show_and_get_dialog(is_flexible=False, shutdown_callback=mock_cb)
        shutdown_btn = self._find_button(dialog, "Shutdown")
        self.assertIsNotNone(shutdown_btn)
        shutdown_btn.clicked.emit()
        mock_cb.assert_called_once()

    def test_non_flexible_no_callback_no_shutdown(self):
        """固定模式无 callback：不应加 Shutdown 按钮"""
        dialog = self._show_and_get_dialog(is_flexible=False, shutdown_callback=None)
        self.assertNotIn("Shutdown", self._button_texts(dialog))

    # ── Ignore 按钮 ────────────────────────────────────────

    def test_ignore_button_always_present(self):
        """弹性/固定模式都应有 Ignore 按钮"""
        dialog = self._show_and_get_dialog(is_flexible=True, shutdown_callback=MagicMock())
        self.assertIsNotNone(self._find_button(dialog, "Ignore"))
        dialog = self._show_and_get_dialog(is_flexible=False, shutdown_callback=MagicMock())
        self.assertIsNotNone(self._find_button(dialog, "Ignore"))

    # ── 窗口属性 ────────────────────────────────────────────

    def test_window_title(self):
        """对话框标题应为 '下班提醒 · Check-out'"""
        dialog = self._show_and_get_dialog(is_flexible=True)
        self.assertEqual(dialog.windowTitle(), "下班提醒 · Check-out")

    def test_minimum_size_set(self):
        """对话框应设置最小尺寸"""
        dialog = self._show_and_get_dialog(is_flexible=False)
        self.assertGreaterEqual(dialog.minimumWidth(), 360)


class TestOtherDialogs(unittest.TestCase):
    """测试其他 ReminderDialog 对话框"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_show_checkin(self):
        """打卡提醒为非模态：show_centered 而非 exec_"""
        from app.ui.dialogs.reminder_dialog import CheckinDialog
        with patch.object(LightDialog, 'show_centered') as mock_show:
            dialog = ReminderDialog.show_checkin()
            mock_show.assert_called_once()
        self.assertIsInstance(dialog, CheckinDialog)

    def test_show_job_record(self):
        """工作记录提醒为非模态：show_centered 而非 exec_"""
        from app.ui.dialogs.reminder_dialog import JobRecordDialog
        with patch.object(LightDialog, 'show_centered') as mock_show:
            dialog = ReminderDialog.show_job_record()
            mock_show.assert_called_once()
        self.assertIsInstance(dialog, JobRecordDialog)

    def test_show_custom_timer_remains_modal(self):
        """自定义计时器结束提醒保持模态（exec_）"""
        from app.ui.dialogs.common import FancyDialog
        with patch.object(FancyDialog, 'exec_') as mock_exec:
            ReminderDialog.show_custom_timer()
            mock_exec.assert_called_once()

    def test_show_update_available_returns_widget(self):
        from PyQt5.QtWidgets import QWidget
        result = ReminderDialog.show_update_available(countdown_seconds=0)
        self.assertIsInstance(result, QWidget)
        result.close()

    def test_show_update_available_defer_callback_on_close(self):
        deferred = [False]
        dialog = ReminderDialog.show_update_available(
            countdown_seconds=0, on_defer=lambda: deferred.__setitem__(0, True))
        dialog.close()
        self.assertTrue(deferred[0])


if __name__ == '__main__':
    unittest.main()
