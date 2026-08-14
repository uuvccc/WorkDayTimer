"""把 images/icon.svg 渲染为 icon.png（256x256）并生成多尺寸 icon.ico。

- icon.png  : 运行时窗口 / 托盘图标（透明背景，保留中心白色猫脸）
- icon.ico  : exe 外壳图标（多尺寸 256/128/64/48/32/16）

依赖：PyQt5（QtSvg）+ Pillow，无需 ImageMagick/wand。
"""
import os

from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(HERE, "images", "icon.svg")
PNG_PATH = os.path.join(HERE, "images", "icon.png")
ICO_PATH = os.path.join(HERE, "images", "icon.ico")

# 超采样 2x 再平滑降采样，边缘抗锯齿更细腻
RENDER_SIZE = 512
OUT_SIZE = 256
ICO_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def render_svg_hi(size):
    with open(SVG_PATH, "rb") as f:
        data = f.read()
    renderer = QSvgRenderer(QByteArray(data))
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)  # 透明背景
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    return img


def main():
    # 需要 Qt GUI 上下文（offscreen / 桌面均可）
    app = QApplication.instance() or QApplication([])

    hi = render_svg_hi(RENDER_SIZE)
    png = hi.scaled(OUT_SIZE, OUT_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    if not png.save(PNG_PATH):
        raise RuntimeError(f"保存 {PNG_PATH} 失败")

    img = Image.open(PNG_PATH).convert("RGBA")
    img.save(ICO_PATH, format="ICO", sizes=ICO_SIZES)

    print(f"已生成 {PNG_PATH} ({OUT_SIZE}x{OUT_SIZE})")
    print(f"已生成 {ICO_PATH} {ICO_SIZES}")


if __name__ == "__main__":
    main()
