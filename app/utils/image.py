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


def _flood_fill_background(white_mask):
    """从图像四条边开始 flood fill，标记与边缘连通的背景区域。

    只返回与边缘连通的白色像素，内部白色区域不会被标记为背景。
    """
    h, w = white_mask.shape
    bg = np.zeros((h, w), dtype=bool)
    # 从四条边上的白色像素开始
    bg[0, :] = white_mask[0, :]
    bg[-1, :] = white_mask[-1, :]
    bg[:, 0] = white_mask[:, 0]
    bg[:, -1] = white_mask[:, -1]

    # 迭代膨胀直到收敛
    for _ in range(h + w):
        expanded = np.zeros_like(bg)
        expanded[1:, :] |= bg[:-1, :]
        expanded[:-1, :] |= bg[1:, :]
        expanded[:, 1:] |= bg[:, :-1]
        expanded[:, :-1] |= bg[:, 1:]
        expanded &= white_mask
        new_bg = bg | expanded
        if np.array_equal(new_bg, bg):
            break
        bg = new_bg

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

    arr = _to_rgba_array(pixmap.toImage())

    r = arr[..., 0].astype(np.float32)
    g = arr[..., 1].astype(np.float32)
    b = arr[..., 2].astype(np.float32)

    # 每个像素到白色 (255,255,255) 的欧氏距离
    dist = np.sqrt((255.0 - r) ** 2 + (255.0 - g) ** 2 + (255.0 - b) ** 2)

    # 距离 -> 不透明度系数（0~1）
    alpha_factor = np.clip((dist - TRANSPARENT_DIST) / (OPAQUE_DIST - TRANSPARENT_DIST),
                           0.0, 1.0)

    # 标记接近白色的像素（用于 flood fill 遍历）
    is_white = dist < OPAQUE_DIST

    # 从边缘 flood fill，找出与边缘连通的背景区域
    is_background = _flood_fill_background(is_white)

    # 只对背景区域应用透明化，内部白色像素保持原样
    orig_alpha = arr[..., 3].astype(np.float32)
    arr[..., 3] = np.where(is_background,
                           (orig_alpha * alpha_factor).astype(np.uint8),
                           arr[..., 3])

    return _from_rgba_array(arr)


def transparent_icon(path):
    """加载图标并去掉白色背景，返回 QIcon。"""
    return QIcon(transparent_pixmap(path))
