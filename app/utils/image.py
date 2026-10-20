"""图片工具：加载图片资源时自动把白色背景转成透明。"""
import math
from collections import deque

from PyQt5.QtGui import QImage, QPixmap, QIcon

# 背景透明化阈值（针对白底 255,255,255）
# 像素到白色的距离 < TRANSPARENT_DIST → 完全透明
# 像素到白色的距离 > OPAQUE_DIST     → 完全不透明
# 两者之间线性过渡，保留抗锯齿边缘的半透明轮廓
TRANSPARENT_DIST = 40.0
OPAQUE_DIST = 140.0

_OPAQUE_DIST_SQ = OPAQUE_DIST * OPAQUE_DIST


def _to_rgba_bytes(image):
    """QImage -> (RGBA bytes 副本, 宽, 高)。"""
    image = image.convertToFormat(QImage.Format_RGBA8888)
    ptr = image.bits()
    ptr.setsize(image.byteCount())
    return bytes(ptr), image.width(), image.height()


def _from_rgba_bytes(data, w, h):
    """RGBA bytes -> QPixmap。"""
    image = QImage(data, w, h, w * 4, QImage.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())


def _flood_fill_background(is_white, w, h):
    """从图像四条边开始 flood fill（BFS），标记与边缘连通的背景区域。

    只返回与边缘连通的白色像素，内部白色区域不会被标记为背景。
    """
    bg = bytearray(w * h)
    queue = deque()

    def _seed(idx):
        if is_white[idx] and not bg[idx]:
            bg[idx] = 1
            queue.append(idx)

    last_row = (h - 1) * w
    for x in range(w):
        _seed(x)
        _seed(last_row + x)
    for y in range(1, h - 1):
        _seed(y * w)
        _seed(y * w + w - 1)

    while queue:
        i = queue.popleft()
        x = i % w
        y = i // w
        if x > 0:
            _seed(i - 1)
        if x < w - 1:
            _seed(i + 1)
        if y > 0:
            _seed(i - w)
        if y < h - 1:
            _seed(i + w)
    return bg


def transparent_pixmap(path_or_pixmap):
    """加载图片并去掉白色背景，返回 QPixmap。

    - 传入路径或 QPixmap 均可；文件不存在或解码失败时原样返回（避免崩溃）。
    - 只处理与图像边缘连通的白色背景，内部白色像素保持不变；
      抗锯齿边缘按到白色的距离线性过渡，保留半透明轮廓。
    """
    if isinstance(path_or_pixmap, QPixmap):
        pixmap = path_or_pixmap
    else:
        pixmap = QPixmap(path_or_pixmap)
    if pixmap.isNull():
        return pixmap

    data, w, h = _to_rgba_bytes(pixmap.toImage())
    n = w * h

    # 距离平方判断"接近白色"（等价 dist < OPAQUE_DIST，避免每像素开方）
    is_white = bytearray(n)
    for i in range(n):
        o = i * 4
        dr = 255 - data[o]
        dg = 255 - data[o + 1]
        db = 255 - data[o + 2]
        if dr * dr + dg * dg + db * db < _OPAQUE_DIST_SQ:
            is_white[i] = 1

    # 从边缘 flood fill，找出与边缘连通的背景区域
    is_background = _flood_fill_background(is_white, w, h)

    # 只对背景区域应用透明化：按到白色的距离线性过渡 alpha；内部白色像素保持原样
    out = bytearray(data)
    sqrt = math.sqrt
    inv_span = 1.0 / (OPAQUE_DIST - TRANSPARENT_DIST)
    for i in range(n):
        if not is_background[i]:
            continue
        o = i * 4
        dr = 255 - data[o]
        dg = 255 - data[o + 1]
        db = 255 - data[o + 2]
        factor = (sqrt(dr * dr + dg * dg + db * db) - TRANSPARENT_DIST) * inv_span
        if factor <= 0.0:
            out[o + 3] = 0
        elif factor < 1.0:
            out[o + 3] = int(data[o + 3] * factor)
        # factor >= 1.0 时 alpha 不变

    return _from_rgba_bytes(bytes(out), w, h)


def transparent_icon(path):
    """加载图标并去掉白色背景，返回 QIcon。"""
    return QIcon(transparent_pixmap(path))
