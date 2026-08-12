"""共享的花哨对话框样式基础设施。

所有提醒/计时器弹窗统一走 FancyDialog：无边框 + 渐变圆角卡片 + emoji + 风格化按钮，
避免每个对话框各写一套重复的 QSS。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QApplication, QGraphicsDropShadowEffect,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


# ── 配色方案：每个弹窗一套渐变 + 主按钮文字色 ──
SCHEMES = {
    # 打卡：早晨暖橙粉
    "sunrise": {
        "gradient": ("#FF9A8B", "#FF6A88"),
        "accent": "#E05A77",
    },
    # 工作记录：冷静蓝青
    "ocean": {
        "gradient": ("#4FACFE", "#00C9FF"),
        "accent": "#0E9BD6",
    },
    # 自定义计时器：计时紫蓝
    "violet": {
        "gradient": ("#8E2DE2", "#4A00E0"),
        "accent": "#6A2FE0",
    },
}


def gradient_qss(c1, c2):
    return (
        "QFrame#frame {"
        "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        f"    stop:0 {c1}, stop:1 {c2});"
        "  border-radius: 16px;"
        "}"
    )


def primary_button_qss(text_color):
    """白色圆角胶囊主按钮。"""
    return (
        "QPushButton {"
        "  background: #ffffff;"
        f"  color: {text_color};"
        "  border: none;"
        "  border-radius: 20px;"
        "  padding: 10px 28px;"
        "  font-size: 15px;"
        "  font-weight: bold;"
        "}"
        "QPushButton:hover { background: #f4f5f7; }"
        "QPushButton:pressed { background: #e6e8eb; }"
    )


def ghost_button_qss():
    """半透明描边辅助按钮。"""
    return (
        "QPushButton {"
        "  background: rgba(255,255,255,0.16);"
        "  color: #ffffff;"
        "  border: 1px solid rgba(255,255,255,0.5);"
        "  border-radius: 18px;"
        "  padding: 8px 18px;"
        "  font-size: 13px;"
        "}"
        "QPushButton:hover { background: rgba(255,255,255,0.30); }"
        "QPushButton:pressed { background: rgba(255,255,255,0.45); }"
    )


def quick_button_qss():
    """半透明白色快捷数字按钮。"""
    return (
        "QPushButton {"
        "  background: rgba(255,255,255,0.22);"
        "  color: #ffffff;"
        "  border: none;"
        "  border-radius: 8px;"
        "  font-size: 14px;"
        "  padding: 8px 0;"
        "  min-width: 0;"
        "}"
        "QPushButton:hover { background: rgba(255,255,255,0.40); }"
        "QPushButton:pressed { background: rgba(255,255,255,0.55); }"
    )


class FancyDialog(QDialog):
    """无边框渐变卡片对话框基类。

    子类向 self.content_layout / self.button_layout 填充内容，
    用 make_button / make_primary_button / add_primary_button 建按钮。
    """

    def __init__(self, title, scheme, parent=None):
        super().__init__(parent)
        c1, c2 = SCHEMES[scheme]["gradient"]
        self._accent = SCHEMES[scheme]["accent"]

        self.setWindowTitle(title)
        # 保留 Qt.Dialog 位，确保是顶层对话框而不是被父窗口裁剪的内嵌子控件
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame()
        self.frame.setObjectName("frame")
        self.frame.setStyleSheet(gradient_qss(c1, c2))
        shadow = QGraphicsDropShadowEffect(self.frame)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.frame.setGraphicsEffect(shadow)
        root.addWidget(self.frame)

        outer = QVBoxLayout(self.frame)
        outer.setContentsMargins(24, 18, 24, 22)
        outer.setSpacing(0)

        # ── 标题行 + 右上角关闭按钮 ──
        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: rgba(255,255,255,0.95); font-size: 15px; font-weight: bold;"
        )
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.22); color: #fff;"
            "  border: none; border-radius: 13px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(255,255,255,0.40); }"
        )
        close_btn.clicked.connect(self.reject)
        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        outer.addLayout(title_row)

        outer.addSpacing(14)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        outer.addLayout(self.content_layout)

        outer.addSpacing(16)

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        outer.addLayout(self.button_layout)

    # ── 内容辅助 ──

    def add_hero(self, emoji, headline, detail):
        """居中大 emoji + 中文粗体主标题 + 英文副标题。"""
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 46px;")
        emoji_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(emoji_label)

        headline_label = QLabel(headline)
        headline_label.setAlignment(Qt.AlignCenter)
        headline_label.setStyleSheet(
            "color: #ffffff; font-size: 19px; font-weight: bold;"
        )
        self.content_layout.addWidget(headline_label)

        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setAlignment(Qt.AlignCenter)
        detail_label.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 13px;")
        self.content_layout.addWidget(detail_label)

    # ── 按钮辅助 ──

    def make_button(self, text, qss, on_click=None):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(qss)
        if on_click:
            btn.clicked.connect(on_click)
        return btn

    def make_primary_button(self, text, on_click=None):
        return self.make_button(text, primary_button_qss(self._accent), on_click)

    def add_primary_button(self, text, on_click=None):
        """添加一个居中的主按钮（适合单一操作的提醒弹窗）。"""
        btn = self.make_primary_button(text, on_click)
        self.button_layout.addStretch()
        self.button_layout.addWidget(btn)
        self.button_layout.addStretch()
        return btn

    def _center_on_screen(self):
        """居中到主屏幕（primary screen），双屏时也不会贴到宠物窗口上。"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(
            screen.x() + (screen.width() - self.width()) // 2,
            screen.y() + (screen.height() - self.height()) // 2,
        )
