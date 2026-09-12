import time
import unittest
from unittest.mock import patch, MagicMock

from PyQt5.QtWidgets import QApplication, QMessageBox

from app.services import update_service
from app.ui.dialogs import settings_dialog as settings_mod
from app.ui.dialogs.settings_dialog import SettingsDialog


class TestManualUpdateCheck(unittest.TestCase):
    """手动「Check for Updates...」不应受 auto_check_update（启动时自动检测）开关影响。"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.dialog = SettingsDialog()

    def tearDown(self):
        self.dialog.close()

    def _wait_until(self, predicate, timeout=3.0):
        """驱动事件循环，等待后台检查线程 + 轮询定时器完成。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.02)
        return predicate()

    def test_manual_check_runs_even_when_auto_disabled(self):
        """关掉自动检测后，手动检查仍应真正发起查询并给出反馈。"""
        fake_config = MagicMock(auto_check_update=False)
        with patch.object(settings_mod, 'config_manager', fake_config), \
                patch.object(update_service, 'check_for_updates',
                             return_value=(False, '1.0.0', '1.0.0')) as mock_check, \
                patch.object(QMessageBox, 'information') as mock_info:
            self.dialog._on_check_updates()
            self.assertTrue(
                self._wait_until(lambda: self.dialog._checking_updates is False),
                "手动检查应在自动检测关闭时依然执行")

        mock_check.assert_called_once()
        mock_info.assert_called_once()

    def test_update_available_prompts_and_invokes_callback(self):
        """检查到新版本：弹确认框，确认后触发下载回调。"""
        callback = MagicMock()
        self.dialog._update_callback = callback
        with patch.object(update_service, 'check_for_updates',
                          return_value=(True, '9.9.9', '1.0.0')), \
                patch.object(QMessageBox, 'question',
                             return_value=QMessageBox.Yes) as mock_question:
            self.dialog._on_check_updates()
            self.assertTrue(
                self._wait_until(lambda: self.dialog._checking_updates is False))

        mock_question.assert_called_once()
        callback.assert_called_once()

    def test_up_to_date_shows_info_without_download(self):
        """已是最新版本：只提示，不下载。"""
        callback = MagicMock()
        self.dialog._update_callback = callback
        with patch.object(update_service, 'check_for_updates',
                          return_value=(False, '1.0.0', '1.0.0')), \
                patch.object(QMessageBox, 'information') as mock_info:
            self.dialog._on_check_updates()
            self.assertTrue(
                self._wait_until(lambda: self.dialog._checking_updates is False))

        mock_info.assert_called_once()
        callback.assert_not_called()


if __name__ == '__main__':
    unittest.main()
