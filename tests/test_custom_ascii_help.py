import unittest
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication

from app.ui import ascii_art
from app.ui.dialogs.custom_ascii_help import CustomAsciiHelpDialog


class TestCustomAsciiHelpDialog(unittest.TestCase):
    """自定义 ASCII 使用说明对话框：内容齐全、按钮行为正确。"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_dialog(self):
        dialog = CustomAsciiHelpDialog()
        dialog.show_centered = MagicMock()
        return dialog

    def test_window_title(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog.windowTitle(), "自定义 ASCII 动画 · Custom Animations")
        dialog.close()

    def test_hero_mentions_folder(self):
        dialog = self._make_dialog()
        self.assertEqual(dialog._headline_label.text(), "自定义 ASCII 动画")
        self.assertIn("ascii_animations/", dialog._detail_label.text())
        dialog.close()

    def test_path_label_points_to_external_dir(self):
        dialog = self._make_dialog()
        self.assertIn(ascii_art.EXTERNAL_SCENES_DIR, dialog._path_label.text())
        dialog.close()

    def test_sample_shows_txt_and_json_formats(self):
        dialog = self._make_dialog()
        text = dialog.sample_text()
        # 两种格式示例都在
        self.assertIn(".txt", text)
        self.assertIn(".json", text)
        # 文本格式关键元素
        self.assertIn("# name:", text)
        self.assertIn("===", text)
        # JSON 格式关键元素
        self.assertIn('"frames"', text)
        self.assertIn('"fps"', text)
        dialog.close()

    def test_open_folder_creates_dir_and_starts(self):
        dialog = self._make_dialog()
        with patch("app.ui.dialogs.custom_ascii_help.os.makedirs") as makedirs, \
             patch("app.ui.dialogs.custom_ascii_help.os.startfile") as startfile:
            dialog._open_folder()
        makedirs.assert_called_once_with(ascii_art.EXTERNAL_SCENES_DIR, exist_ok=True)
        startfile.assert_called_once_with(ascii_art.EXTERNAL_SCENES_DIR)
        dialog.close()


if __name__ == '__main__':
    unittest.main()
