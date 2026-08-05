"""图片工具：加载图片资源时自动把白色背景转成透明。"""
import numpy as np
from PyQt5.QtGui import QImage, QPixmap, QIcon

# 背景透明化阈值（针对白底 255,255,255）
# 像素到白色的距离 < TRANSPARENT_DIST → 完全透明
# 像素到白色的距离 > OPAQUE_DIST     → 完全不透明
# 两者之间线性过渡，保留抗锯齿边缘的半透明轮廓
TRANSPARENT_DIST = 40.0
OPAQUE_DIST = 140.0


def _to_rgba_array(image):
    """QImage -> RGBA numpy 数组（返回可写副本）。"""
    image = image.convertToFormat(QImage.Format_RGBA8888)
    w, h = image.width(), image.height()
    ptr = image.bits()
    ptr.setsize(image.byteCount())
    return np.frombuffer(ptr, np.uint8).reshape((h, w, 4)).copy()


def _from_rgba_array(arr):
    """RGBA numpy 数组 -> QPixmap。"""
    h, w = arr.shape[:2]
    image = QImage(arr.data, w, h, arr.strides[0], QImage.Format_RGBA8888)
    return QPixmap.fromImage(image.copy())


def transparent_pixmap(path_or_pixmap):
    """加载图片并去掉白色背景，返回 QPixmap。

    - 传入路径或 QPixmap 均可；文件不存在或解码失败时原样返回（避免崩溃）。
    - 只有接近白色的像素变透明，图片主体颜色不受影响；
      抗锯齿边缘按到白色的距离线性过渡，保留半透明轮廓。
    """
    if isinstance(path_or_pixmap, QPixmap):
        pixmap = path_or_pixmap
    else:
        pixmap = QPixmap(path_or_pixmap)
    if pixmap.isNull():
        return pixmap

    arr = _to_rgba_array(pixmap.toImage())

    r = arr[..., 0].astype(np.float32)
    g = arr[..., 1].astype(np.float32)
    b = arr[..., 2].astype(np.float32)

    # 每个像素到白色 (255,255,255) 的欧氏距离
    dist = np.sqrt((255.0 - r) ** 2 + (255.0 - g) ** 2 + (255.0 - b) ** 2)

    # 距离 -> 不透明度系数（0~1）
    alpha_factor = np.clip((dist - TRANSPARENT_DIST) / (OPAQUE_DIST - TRANSPARENT_DIST),
                           0.0, 1.0)

    # 与图片原有的 alpha 相乘（保留原图自带的半透明区域）
    arr[..., 3] = (arr[..., 3].astype(np.float32) * alpha_factor).astype(np.uint8)

    return _from_rgba_array(arr)


def transparent_icon(path):
    """加载图标并去掉白色背景，返回 QIcon。"""
    return QIcon(transparent_pixmap(path))
