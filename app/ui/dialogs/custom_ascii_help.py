"""自定义 ASCII 动画使用说明对话框（浅色非模态）。

不改动任何功能，只把「如何添加自定义动画」写清楚：
- 文件放哪（ascii_animations/ 文件夹，可一键打开）
- 两种格式示例（.txt 纯文本 / .json）
- 怎么让动画生效（托盘 Reload Animations 或重启）
- 怎么验证（logs/app.log 关键字）
"""
import os

from PyQt5.QtWidgets import (
    QLabel, QPlainTextEdit, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

from app.ui import ascii_art
from app.ui.dialogs.common import LightDialog
from app.utils.logger import logger


# 示例内容：纯文本 + JSON 两种格式，与 ascii_animations/README.md 保持一致
_EXAMPLE_TEXT = """示例一：新建 my_pet.txt（简单）
# name: my_pet      ← 场景名（可选，默认用文件名）
# color: #FF0000    ← 单色主色（可选，默认黑色）
# fps: 4            ← 播放帧率（可选，默认 2）
# rainbow: false    ← true 时逐行彩色渐变（可选）
# idle: true        ← false 时不参与待机轮换（可选）
===
   /\\_/\\
  ( o o )
   \\_^_/
===
   /\\_/\\
  ( - - )
   \\_^_/
（帧之间用单独一行 === 分隔）

示例二：新建 my_pet.json（进阶，字段同上）
{
  "name": "my_pet",
  "color": "#FF0000",
  "fps": 4,
  "rainbow": false,
  "idle": true,
  "frames": [
    ["   /\\\\_/\\\\   ", "  ( o o )  ", "   \\\\_^_/   "],
    ["   /\\\\_/\\\\   ", "  ( - - )  ", "   \\\\_^_/   "]
  ]
}"""

_STEPS = (
    "① 打开 ascii_animations 文件夹（点下方按钮）\n"
    "② 在里面新建一个 .txt 或 .json 文件（格式见下方示例）\n"
    "③ 右键托盘图标 → Reload Animations，新动画立即生效（重启应用也会自动加载）\n"
    "④ 验证：logs/app.log 中看到 External ascii scene loaded 即加载成功"
)

_TIPS = (
    "提示：文件名以 _ 或 . 开头会被忽略（可放草稿）；"
    "与内置场景同名时以你的文件为准；"
    "加载失败会记录到 logs/app.log（External ascii scene load failed: <原因>）。"
)


class CustomAsciiHelpDialog(LightDialog):
    """「Custom Animations...」使用说明弹窗。"""

    def __init__(self, parent=None):
        super().__init__("自定义 ASCII 动画 · Custom Animations", parent)
        logger.debug("CustomAsciiHelpDialog opening")
        self._build_body()
        self._build_buttons()

    # ── 内容区 ────────────────────────────────────────────

    def _build_body(self):
        self.setMinimumWidth(560)

        self.add_hero("🎨", "自定义 ASCII 动画",
                      "把动画文件放进 ascii_animations/ 文件夹即可")

        steps = QLabel(_STEPS)
        steps.setWordWrap(True)
        steps.setStyleSheet(
            "color: #444444; font-size: 13px; line-height: 1.6;"
            "background: #f7f8fa; border: 1px solid #e6e8eb;"
            "border-radius: 8px; padding: 10px 12px;"
        )
        self.content_layout.addWidget(steps)

        # 文件夹路径 + 打开按钮
        path_row = QLabel(
            "动画文件夹：" + ascii_art.EXTERNAL_SCENES_DIR)
        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono.setPointSize(10)
        path_row.setFont(mono)
        path_row.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_row.setStyleSheet("color: #777777;")
        self.content_layout.addWidget(path_row)

        sample_title = QLabel("文件格式示例（可直接复制修改）")
        sample_title.setStyleSheet(
            "color: #222222; font-size: 13px; font-weight: bold;")
        self.content_layout.addWidget(sample_title)

        sample = QPlainTextEdit()
        sample.setReadOnly(True)
        sample.setPlainText(_EXAMPLE_TEXT)
        sample.setFont(mono)
        sample.setFixedHeight(190)
        sample.setStyleSheet(
            "QPlainTextEdit { background: #f7f8fa; color: #333333;"
            "  border: 1px solid #e6e8eb; border-radius: 8px;"
            "  padding: 8px; }"
        )
        self.content_layout.addWidget(sample)

        tips = QLabel(_TIPS)
        tips.setWordWrap(True)
        tips.setStyleSheet("color: #888888; font-size: 12px;")
        self.content_layout.addWidget(tips)

        # 记录下用于测试的引用
        self._sample_edit = sample
        self._path_label = path_row

    # ── 底部按钮行 ───────────────────────────────────────

    def _build_buttons(self):
        open_btn = self.make_button("打开文件夹", on_click=self._open_folder)
        done_btn = self.make_primary_button("完成 OK", on_click=self.accept)

        self.button_layout.addWidget(open_btn)
        self.button_layout.addStretch()
        self.button_layout.addWidget(done_btn)

    # ── 逻辑 ────────────────────────────────────────────

    def _open_folder(self):
        """打开（必要时先创建）ascii_animations/ 文件夹。"""
        directory = ascii_art.EXTERNAL_SCENES_DIR
        try:
            os.makedirs(directory, exist_ok=True)
            os.startfile(directory)
        except OSError as e:
            logger.error("Failed to open ascii folder %s: %s", directory, e)
            QMessageBox.warning(self, "无法打开文件夹", str(e))

    def sample_text(self):
        """供测试/调试使用：返回示例文本。"""
        return self._sample_edit.toPlainText()
