import unittest

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor, QImage, QPixmap

from app.utils.image import transparent_pixmap


class TestTransparentPixmap(unittest.TestCase):
    """白色背景透明化：边缘连通背景变透明，内部白色孤岛保持不变。"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_pixmap(self, w=64, h=64, red_block=True, white_island=True):
        img = QImage(w, h, QImage.Format_RGBA8888)
        img.fill(QColor(255, 255, 255, 255))
        if red_block:
            for y in range(16, 48):
                for x in range(16, 48):
                    img.setPixelColor(x, y, QColor(255, 0, 0, 255))
            if white_island:
                # 红色块内部的白色孤岛：与边缘不连通，不应被透明化
                for y in range(28, 36):
                    for x in range(28, 36):
                        img.setPixelColor(x, y, QColor(255, 255, 255, 255))
        return QPixmap.fromImage(img.copy())

    def _alpha_at(self, pixmap, x, y):
        img = pixmap.toImage().convertToFormat(QImage.Format_RGBA8888)
        return img.pixelColor(x, y).alpha()

    def test_border_connected_white_becomes_transparent(self):
        result = transparent_pixmap(self._make_pixmap())
        self.assertEqual(self._alpha_at(result, 0, 0), 0)
        self.assertEqual(self._alpha_at(result, 5, 5), 0)

    def test_opaque_content_alpha_preserved(self):
        result = transparent_pixmap(self._make_pixmap())
        self.assertEqual(self._alpha_at(result, 32, 20), 255)  # 红色块

    def test_enclosed_white_island_not_transparent(self):
        result = transparent_pixmap(self._make_pixmap())
        self.assertEqual(self._alpha_at(result, 32, 32), 255)  # 白色孤岛

    def test_all_white_image_becomes_fully_transparent(self):
        result = transparent_pixmap(self._make_pixmap(red_block=False))
        self.assertEqual(self._alpha_at(result, 0, 0), 0)
        self.assertEqual(self._alpha_at(result, 32, 32), 0)

    def test_missing_file_returns_null_pixmap_without_crash(self):
        result = transparent_pixmap("nonexistent_dir/nonexistent.png")
        self.assertTrue(result.isNull())


if __name__ == "__main__":
    unittest.main()
