"""共享对话框基础设施（标准 Windows 风格）。

所有弹窗统一为原生标题栏 + 原生控件的 Windows 对话框，
不再使用无边框渐变卡片与自定义按钮 QSS。
保留旧类名 FancyDialog / LightDialog 及其接口（调用方与测试依赖）。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication,
)
from PyQt5.QtCore import Qt


class FancyDialog(QDialog):
    """Windows 风格对话框基类（原生标题栏 + 原生控件）。

    子类向 self.content_layout / self.button_layout 填充内容，
    用 make_button / make_primary_button / add_primary_button 建按钮。
    模态用法 exec_()；非模态见 LightDialog。
    """

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        # 原生对话框标题栏；置顶保持提醒可见（与旧行为一致）
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(360)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(8)
        root.addLayout(self.content_layout)

        root.addStretch()

        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(8)
        root.addLayout(self.button_layout)

    # ── 内容辅助 ──

    def add_hero(self, emoji, headline, detail):
        """消息框式布局：左侧 emoji 图标 + 粗体标题 + 灰色说明文字。"""
        row = QHBoxLayout()
        row.setSpacing(12)

        icon_label = QLabel(emoji)
        icon_label.setStyleSheet("font-size: 28px;")
        icon_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        row.addWidget(icon_label, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        headline_label = QLabel(headline)
        headline_label.setWordWrap(True)
        headline_font = headline_label.font()
        headline_font.setBold(True)
        headline_label.setFont(headline_font)
        text_col.addWidget(headline_label)

        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("color: #666666;")
        text_col.addWidget(detail_label)
        text_col.addStretch()

        row.addLayout(text_col, 1)
        self.content_layout.addLayout(row)

        self._headline_label = headline_label
        self._detail_label = detail_label

    # ── 按钮辅助 ──

    def make_button(self, text, primary=False, on_click=None):
        btn = QPushButton(text)
        if primary:
            btn.setDefault(True)
        if on_click:
            btn.clicked.connect(on_click)
        return btn

    def make_primary_button(self, text, on_click=None):
        return self.make_button(text, primary=True, on_click=on_click)

    def add_primary_button(self, text, on_click=None):
        """添加一个右对齐的主按钮（Windows 约定：主按钮靠右）。"""
        btn = self.make_primary_button(text, on_click)
        self.button_layout.addStretch()
        self.button_layout.addWidget(btn)
        return btn

    def add_button(self, text, on_click=None):
        """添加一个普通按钮（不改变对齐，由调用方控制位置）。"""
        return self.make_button(text, primary=False, on_click=on_click)

    def _center_on_screen(self):
        """居中到主屏幕（primary screen），双屏时也不会贴到宠物窗口上。"""
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        self.move(
            screen.x() + (screen.width() - self.width()) // 2,
            screen.y() + (screen.height() - self.height()) // 2,
        )


def center_on_screen(widget, width=None, height=None):
    """把任意顶层窗口居中到主屏幕（primary screen）。"""
    screen = QApplication.primaryScreen().availableGeometry()
    if width and height:
        widget.resize(width, height)
    else:
        widget.adjustSize()
    widget.move(
        screen.x() + (screen.width() - widget.width()) // 2,
        screen.y() + (screen.height() - widget.height()) // 2,
    )


class LightDialog(FancyDialog):
    """非模态 Windows 风格对话框基类。

    - 非模态：show() 显示，不阻塞主界面
    - 显示前调用 show_centered() 居中到主屏幕
    - 子类向 self.content_layout / self.button_layout 填充内容
    """

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

    # ── 显示 ──

    def show_centered(self, width=None, height=None):
        """居中到主屏幕后以非模态方式显示。"""
        center_on_screen(self, width, height)
        self.show()
        self.raise_()
        self.activateWindow()
