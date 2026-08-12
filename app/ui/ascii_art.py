"""ASCII 字符动画场景库与渲染器。

宠物窗口用纯字符（等宽字体）逐帧播放动画。场景定义在 SCENES 里，
每帧是一个字符网格（list[str]），播放前统一 pad 成等宽等高，避免跳动。
渲染支持两种风格：
- 单色：多行纯文本，由 QLabel 的 QSS color 着色；
- rainbow：每行一个颜色（场景色→白色渐变），输出富文本 <span>。
"""
import html

# ── 场景库 ────────────────────────────────────────────────
# color   : 单色风格主色（hex）
# fps     : 播放帧率（帧/秒）
# rainbow : 是否逐行渐变着色
# frames  : 每帧为一个 list[str]，行与行对齐（宽度不一致会由 normalize 补齐）
SCENES = {
    "cat": {
        "color": "#FF9A8B",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["        ", "  /\\_/\\  ", " ( o.o ) ", "  > ^ <  ", "        "],
            ["        ", "  /\\_/\\  ", " ( -.- ) ", "  > ^ <  ", "        "],
            [" /\\_/\\  ", " ( o.o ) ", "  > ^ <  ", "        ", "        "],
            [" /\\_/\\  ", " ( ^.^ ) ", "  > ^ <  ", "        ", "        "],
        ],
    },
    "bunny": {
        "color": "#F9A8D4",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["  /\\_/\\  ", " ( o.o ) ", "  ( U U )", "        "],
            ["  /\\_/\\  ", " ( o.o )\\", "  ( U U )", "        "],
            ["  /\\_/\\  ", "/( o.o ) ", "  ( U U )", "        "],
        ],
    },
    "clock": {
        "color": "#38BDF8",
        "fps": 2,
        "rainbow": True,
        "frames": [
            ["  .----.", " /      \\", "| 12    |", "|  ^    |",
             " \\      /", "  '----'"],
            ["  .----.", " /      \\", "| 12    |", "|  ->   |",
             " \\      /", "  '----'"],
            ["  .----.", " /      \\", "| 12    |", "|  v    |",
             " \\      /", "  '----'"],
            ["  .----.", " /      \\", "| 12    |", "|  <-   |",
             " \\      /", "  '----'"],
        ],
    },
    "coffee": {
        "color": "#C98A4B",
        "fps": 2,
        "rainbow": True,
        "frames": [
            ["   ~ ~ ~  ", "  .-~~~-. ", " /       \\", "|  c   c  |",
             " \\       /", "  '-~-~-' "],
            ["    ~ ~   ", "  .-~~~-. ", " /       \\", "|  c   c  |",
             " \\       /", "  '-~-~-' "],
            ["          ", "  .-~~~-. ", " /       \\", "|  c   c  |",
             " \\       /", "  '-~-~-' "],
            ["   ~ ~ ~  ", "  .-~~~-. ", " /       \\", "|  c   c  |",
             " \\       /", "  '-~-~-' "],
        ],
    },
    "worker": {
        "color": "#A78BFA",
        "fps": 3,
        "rainbow": False,
        "frames": [
            [" ( o.o ) ", "  /|_|\\  ", "  _|_|_  "],
            [" ( o.o ) ", "  \\|_|/  ", "  _|_|_  "],
            [" ( -.- ) ", "  /|_|\\  ", "  _|_|_  "],
            [" ( o.o ) ", "  _|_|_  ", "  _|_|_  "],
        ],
    },
    "sleepy": {
        "color": "#818CF8",
        "fps": 2,
        "rainbow": False,
        "frames": [
            [" z Z z ", " ( -_- )", "        "],
            ["   Z z ", " ( -_- )", "        "],
            ["       ", " ( -_- )", "  z Z z "],
            ["       ", " ( -_- )", "        "],
        ],
    },
    "celebrate": {
        "color": "#FBBF24",
        "fps": 4,
        "rainbow": True,
        "frames": [
            ["   *   *  ", "  \\  |  / ", "   ( o.o )", "  /  |  \\ ", "   *   *  "],
            [" *  *  *  ", "   \\ | /  ", "  ( ^.^ ) ", "   / | \\  ", " *  *  *  "],
            ["   *   *  ", "  *  |  * ", "   ( ^.^ )", "  *  |  * ", "   *   *  "],
            ["         ", "  \\  |  / ", "   ( o.o )", "  /  |  \\ ", "         "],
        ],
    },
}

# 待机场景：平时随机轮换这些（替代原图片 60s 随机换图）
IDLE_SCENES = ["cat", "bunny", "coffee", "worker"]


# ── 归一化：所有帧 pad 成统一网格 ─────────────────────────

def normalize():
    """把所有场景的帧补齐到统一宽高，避免逐帧播放时文字跳动。"""
    for scene in SCENES.values():
        frames = scene["frames"]
        max_h = max(len(f) for f in frames)
        max_w = max(max(len(r) for r in f) for f in frames)
        for f in frames:
            while len(f) < max_h:
                f.append("")
            for i, row in enumerate(f):
                f[i] = row.ljust(max_w)
        scene["_width"] = max_w
        scene["_height"] = max_h


normalize()


# ── 颜色工具 ──────────────────────────────────────────────

def _lerp_hex(c1, c2, t):
    """两个 #RRGGBB 颜色之间线性插值，t∈[0,1]。"""
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    ch = lambda a, b: int(a + (b - a) * t)
    return "#%02X%02X%02X" % (ch(r1, r2), ch(g1, g2), ch(b1, b2))


def _row_colors(color, n):
    """场景色 → 浅色的 n 个渐变色（rainbow 逐行用）。"""
    if n <= 1:
        return [color]
    steps = [i / (n - 1) for i in range(n)]
    return [_lerp_hex(color, "#FFFFFF", t * 0.75) for t in steps]


# ── 渲染 ──────────────────────────────────────────────────

def render_frame(scene, index):
    """返回场景第 index 帧的显示文本。

    rainbow 场景返回富文本（每行一个 <span> 颜色 + <br>），
    否则返回多行纯文本（颜色由 QLabel 的 QSS 控制）。
    """
    frame = scene["frames"][index % len(scene["frames"])]
    if scene.get("rainbow"):
        colors = _row_colors(scene["color"], len(frame))
        lines = [f'<span style="color:{c}">{html.escape(row)}</span>'
                 for row, c in zip(frame, colors)]
        return "<br>".join(lines)
    return "\n".join(frame)
