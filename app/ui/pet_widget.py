"""桌面宠物显示组件（混合式设计）。

顶部宠物头像（随状态动效）→ 中部环形进度（当天工作进度）→
环心 HH:MM:SS 倒计时 → 底部中文状态文案。

本模块为纯展示层：MainWindow 每 250ms 调用 set_view() 传入数据，
PetWidget 内部完成状态机驱动 + 动画 + 自定义绘制，不关心计时逻辑。
状态机 / 时间格式化抽成模块级纯函数，便于脱离 GUI 单元测试。
"""
import math

from PyQt5.QtCore import (
    Qt, QPoint, QPointF, QRectF, QAbstractAnimation, QVariantAnimation, pyqtSignal,
)
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PyQt5.QtWidgets import QWidget

from app.config.constants import ICON_FILE
from app.utils.image import transparent_pixmap

# ── 状态定义 ─────────────────────────────────────────────

PET_STATES = ("idle", "working", "near_end", "done", "custom")


def resolve_state(remaining_work_sec, work_progress, custom_active, total_work_sec):
    """根据剩余秒数 / 进度 / 自定义计时器状态解析宠物状态。

    - 自定义倒计时激活 → "custom"（覆盖工作计时显示）
    - 剩余 <= 0  → "done"（已下班）
    - 剩余 > 总时长 → "idle"（固定模式下尚未到上班开始时间）
    - 剩余 < 1 小时 或 进度 >= 80% → "near_end"（临近下班）
    - 其余 → "working"
    """
    if custom_active:
        return "custom"
    if remaining_work_sec <= 0:
        return "done"
    if remaining_work_sec > total_work_sec:
        return "idle"
    if remaining_work_sec < 3600 or work_progress >= 80:
        return "near_end"
    return "working"


def format_hms(total_sec):
    """秒数 → 恒 8 字符的 HH:MM:SS（负值/0 → '00:00:00'）。"""
    s = max(0, int(total_sec))
    hours, rem = divmod(s, 3600)
    minutes, secs = divmod(rem, 60)
    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)


# 状态 → 主题元数据（环色 / 动效 / 默认文案）
STATE_META = {
    "idle":     {"color": QColor(120, 160, 220), "mood": "breathe",     "label": "等待开工"},
    "working":  {"color": QColor(70, 180, 120),  "mood": "bounce",      "label": "工作中"},
    "near_end": {"color": QColor(240, 160, 60),  "mood": "bounce_fast", "label": "快下班啦"},
    "done":     {"color": QColor(90, 200, 130),  "mood": "celebrate",   "label": "已下班"},
    "custom":   {"color": QColor(150, 120, 210), "mood": "bounce",      "label": "自定义倒计时"},
}

# 动效 → 动画参数（values 为 start / 中程 / end，loop=-1 无限循环）
MOOD_ANIM = {
    "breathe":     {"duration": 2000, "values": (0.0, 1.0, 0.0), "loop": -1},
    "bounce":      {"duration": 700,  "values": (0.0, 1.0, 0.0), "loop": -1},
    "bounce_fast": {"duration": 350,  "values": (0.0, 1.0, 0.0), "loop": -1},
    "celebrate":   {"duration": 600,  "values": (0.4, 1.0, 0.4), "loop": -1},
}

# ── 布局常量（窗口固定 200x200）─────────────────────────
AVATAR_SIZE = 60.0
RING_CENTER = QPointF(100.0, 118.0)
RING_RADIUS = 50.0
RING_PEN_WIDTH = 10.0


class PetWidget(QWidget):
    """混合式桌面宠物显示组件。

    交互：
    - 左键拖拽移动窗口（直接操作顶层窗口）
    - 右键弹出 context_menu_requested 信号，由 MainWindow 弹托盘菜单
    - setFocusPolicy(NoFocus)，不抢键盘焦点（Enter 切 QQ 仍走 MainWindow）
    """

    context_menu_requested = pyqtSignal(QPoint)  # globalPos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.NoFocus)

        # 展示数据
        self._state = "idle"
        self._progress = 0.0
        self._remaining_sec = 0
        self._status_text = ""
        self._tooltip = ""

        # 头像（白底自动转透明），加载失败时用兜底图形
        self._avatar = transparent_pixmap(ICON_FILE)
        if not self._avatar.isNull():
            self._avatar.setDevicePixelRatio(self.devicePixelRatioF())

        # 字体：等宽数字防抖动
        self._font_time = QFont("Consolas", 15, QFont.Bold)
        self._font_status = QFont("Microsoft YaHei", 8)

        # 拖拽
        self._drag_offset = QPoint()

        # 动效：单一 QVariantAnimation 复用，仅动画态 start，静态不空转
        self._anim = QVariantAnimation(self)
        self._anim.valueChanged.connect(self.update)

    # ── 对外接口 ─────────────────────────────────────────

    def set_view(self, state, progress, remaining_sec, status_text, tooltip=""):
        """MainWindow 定时调用：更新展示数据并触发重绘。"""
        if state != self._state:
            self._start_mood_anim(STATE_META[state]["mood"])
        self._state = state
        self._progress = min(100.0, max(0.0, float(progress)))
        self._remaining_sec = max(0, int(remaining_sec))
        self._status_text = status_text
        if tooltip and tooltip != self._tooltip:
            self._tooltip = tooltip
            self.setToolTip(tooltip)
        self.update()

    # ── 动画 ─────────────────────────────────────────────

    def _start_mood_anim(self, mood):
        cfg = MOOD_ANIM[mood]
        self._anim.stop()
        self._anim.setDuration(cfg["duration"])
        self._anim.setStartValue(cfg["values"][0])
        self._anim.setEndValue(cfg["values"][-1])
        self._anim.setKeyValueAt(0.5, cfg["values"][1])
        self._anim.setLoopCount(cfg["loop"])
        self._anim.start()

    def _anim_value(self):
        """当前动画值 t；动画未运行时取中间值 0.5（静态展示）。"""
        if self._anim.state() == QAbstractAnimation.Running:
            return self._anim.currentValue()
        return 0.5

    # ── 绘制 ─────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        theme = STATE_META[self._state]
        mood = theme["mood"]
        t = self._anim_value()

        self._draw_ring(painter, theme["color"], mood, t)
        self._draw_avatar(painter, mood, t)
        self._draw_time(painter, theme["color"])
        self._draw_status(painter, theme["color"])
        painter.end()

    def _draw_ring(self, painter, color, mood, t):
        ring_rect = QRectF(
            RING_CENTER.x() - RING_RADIUS,
            RING_CENTER.y() - RING_RADIUS,
            RING_RADIUS * 2,
            RING_RADIUS * 2,
        )
        # 背景整圆（低透明主题色）
        bg_pen = QPen(QColor(color.red(), color.green(), color.blue(), 28))
        bg_pen.setWidthF(RING_PEN_WIDTH)
        bg_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(ring_rect, 0, 360 * 16)

        # 进度弧（从顶部顺时针），idle 呼吸态 alpha 随 t 脉动
        prog_color = QColor(color)
        if mood == "breathe":
            prog_color.setAlphaF(0.35 + 0.65 * t)
        prog_pen = QPen(prog_color)
        prog_pen.setWidthF(RING_PEN_WIDTH)
        prog_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(prog_pen)
        sweep = -int(self._progress * 3.6 * 16)  # progress% → 角度(1/16 度)
        painter.drawArc(ring_rect, 90 * 16, sweep)

    def _draw_avatar(self, painter, mood, t):
        y_offset = 0.0
        scale = 1.0
        if mood in ("bounce", "bounce_fast"):
            y_offset = -6.0 * math.sin(math.pi * t)
        elif mood == "celebrate":
            scale = 0.9 + 0.1 * t
        elif mood == "breathe":
            y_offset = -2.0 * math.sin(math.pi * t)

        size = AVATAR_SIZE * scale
        avatar_rect = QRectF(
            RING_CENTER.x() - size / 2,
            RING_CENTER.y() - RING_RADIUS - size / 2 + y_offset,
            size,
            size,
        )
        if self._avatar.isNull():
            # 兜底：头像缺失时画主题色圆
            painter.setBrush(QColor(180, 190, 200))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(avatar_rect)
            return
        painter.drawPixmap(avatar_rect.toRect(), self._avatar)

    def _draw_time(self, painter, color):
        painter.setFont(self._font_time)
        painter.setPen(color)
        time_text = format_hms(self._remaining_sec)
        fm = QFontMetrics(self._font_time)
        text_w = fm.horizontalAdvance("00:00:00")
        time_rect = QRectF(
            RING_CENTER.x() - text_w / 2,
            RING_CENTER.y() - fm.height() / 2,
            text_w,
            fm.height(),
        )
        painter.drawText(time_rect, Qt.AlignCenter, time_text)

    def _draw_status(self, painter, color):
        painter.setFont(self._font_status)
        painter.setPen(color)
        status_rect = QRectF(10.0, RING_CENTER.y() + RING_RADIUS + 6, 180.0, 22.0)
        painter.drawText(status_rect, Qt.AlignCenter, self._status_text)

    # ── 交互 ─────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and not self._drag_offset.isNull():
            self.window().move(event.globalPos() - self._drag_offset)

    def contextMenuEvent(self, event):
        self.context_menu_requested.emit(event.globalPos())
