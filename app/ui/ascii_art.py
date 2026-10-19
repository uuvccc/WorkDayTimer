"""ASCII 字符动画场景库与渲染器。

宠物窗口用纯字符（等宽字体）逐帧播放动画。所有场景都以文件形式存放，
启动时统一加载进 SCENES，每帧是一个字符网格（list[str]），播放前统一
pad 成等宽等高，避免跳动。

动画文件有两个来源，同名时以用户文件为准：
- 内置默认动画：随应用分发的只读资源，exe 模式由 --add-data 打包进 exe，
  运行时从 ``sys._MEIPASS`` 读取；源码运行（开发/测试）时就是项目根的
  ``ascii_animations/`` 文件夹。
- 用户自定义动画：exe/项目根目录下的 ``ascii_animations/`` 文件夹，
  启动时（以及托盘 Reload Animations）自动加载。

渲染支持两种风格：
- 单色：多行纯文本，由 QLabel 的 QSS color 着色；
- rainbow：每行一个颜色（场景色→白色渐变），输出富文本 <span>。

支持两种文件格式：
- ``.json``：结构化定义（name/color/fps/rainbow/idle/frames）
- ``.txt`` / ``.ascii``：``# 键: 值`` 元数据 + ``===`` 帧分隔线的纯文本格式
文件名以 ``_`` 或 ``.`` 开头的文件会被跳过；解析失败的文件记日志并跳过，
不影响启动。格式详见 ``ascii_animations/README.md``。
"""
import html
import json
import os

from app.config.constants import BASE_DIR, RESOURCE_DIR
from app.utils.logger import logger

# ── 场景注册表 ────────────────────────────────────────────
# 所有动画（内置默认 + 用户自定义）启动时从动画文件加载进来：
# color   : 单色风格主色（hex）
# fps     : 播放帧率（帧/秒）
# rainbow : 是否逐行渐变着色
# frames  : 每帧为一个 list[str]，行与行对齐（宽度不一致会由 normalize 补齐）
SCENES = {}

# 待机场景：平时随机轮换这些；idle 未设为 false 的场景加载后自动追加
IDLE_SCENES = []


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


# ── 动画文件导入 ─────────────────────────────────────────
# 内置默认动画与用户自定义动画都通过 load_external_scenes() 扫描加载。

# 用户可写目录（exe 旁边 / 项目根），放用户自定义动画
EXTERNAL_SCENES_DIR = os.path.join(BASE_DIR, "ascii_animations")

# 内置默认动画目录：源码运行时与用户目录是同一个文件夹；
# exe 模式下 --add-data 打包的默认动画被解压到 sys._MEIPASS（只读）
BUNDLED_SCENES_DIR = os.path.join(RESOURCE_DIR, "ascii_animations")

# 文本格式元数据允许的键
_TEXT_META_KEYS = ("color", "fps", "rainbow", "name", "idle")


def _parse_external_json(path):
    """解析外部 JSON 场景文件，返回 (name, scene)。

    格式：{"name": 可选, "color": "#000000", "fps": 2,
           "rainbow": false, "idle": true, "frames": [["行1", "行2"], ...] 或单帧字符串}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "frames" not in data:
        raise ValueError("JSON 场景需要 frames 字段")
    raw_frames = data["frames"]
    if isinstance(raw_frames, str):
        raw_frames = [raw_frames]
    frames = []
    for raw_frame in raw_frames:
        if isinstance(raw_frame, str):
            frames.append(raw_frame.splitlines())
        elif isinstance(raw_frame, (list, tuple)):
            if not all(isinstance(r, str) for r in raw_frame):
                raise ValueError("帧内容必须全部是字符串")
            frames.append(list(raw_frame))
        else:
            raise ValueError("不支持的帧格式: {}".format(type(raw_frame).__name__))
    if not frames or any(not f for f in frames):
        raise ValueError("frames 不能为空")
    name = str(data.get("name") or os.path.splitext(os.path.basename(path))[0]).strip()
    scene = {
        "color": str(data.get("color", "#000000")),
        "fps": max(1, int(data.get("fps", 2))),
        "rainbow": bool(data.get("rainbow", False)),
        "frames": frames,
    }
    if not data.get("idle", True):
        scene["_external_no_idle"] = True
    return name, scene


def _parse_external_text(path):
    """解析外部文本场景文件，返回 (name, scene)。

    格式：元数据行必须写在第一个帧分隔线之前，帧之间用单独一行 ``===``
    （或 ``---``）分隔；没有分隔线时整个文件视为单帧。

        # name: my_pet        ← 可选，缺省用文件名
        # color: #FF0000      ← 可选，缺省 #000000
        # fps: 3              ← 可选，缺省 2
        # rainbow: false      ← 可选，缺省 false
        # idle: false         ← 可选，false 时不加入待机轮换
        ===
        第 1 帧内容...
        ===
        第 2 帧内容...
    """
    meta = {"color": "#000000", "fps": 2, "rainbow": False, "idle": True}
    frames = []
    current = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            stripped = line.strip()
            if not frames and stripped.startswith("#"):
                body = stripped.lstrip("#").strip()
                if ":" in body:
                    key, _, value = body.partition(":")
                    key = key.strip().lower()
                    value = value.strip()
                    if key in _TEXT_META_KEYS:
                        if key in ("color", "name"):
                            meta[key] = value
                        elif key == "fps":
                            meta[key] = max(1, int(value))
                        else:
                            meta[key] = value.lower() in ("1", "true", "yes", "on")
                continue
            if stripped in ("===", "---"):
                if current:
                    frames.append(current)
                    current = []
                continue
            current.append(line)
    if current:
        frames.append(current)
    if not frames:
        raise ValueError("没有解析到任何帧")
    name = str(meta.get("name") or os.path.splitext(os.path.basename(path))[0]).strip()
    scene = {
        "color": meta["color"],
        "fps": meta["fps"],
        "rainbow": meta["rainbow"],
        "frames": frames,
    }
    if not meta["idle"]:
        scene["_external_no_idle"] = True
    return name, scene


def load_external_scenes(directory=None):
    """扫描动画目录，把合法的动画注册进 SCENES 并返回加载的场景名列表。

    - 支持 ``.json`` / ``.txt`` / ``.ascii`` 文件；
    - 文件名以 ``_`` 或 ``.`` 开头的文件跳过（方便放未完成的动画）；
    - 同名场景会覆盖已加载的场景（以本次加载的文件为准）；
    - 解析失败的文件记录日志并跳过，不影响启动；
    - 默认加入待机轮换，除非文件里声明 ``idle: false``。
    """
    if directory is None:
        directory = EXTERNAL_SCENES_DIR
    loaded = []
    os.makedirs(directory, exist_ok=True)
    for filename in sorted(os.listdir(directory)):
        if filename.startswith((".", "_")):
            continue
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            continue
        lower = filename.lower()
        if lower.endswith(".json"):
            parse = _parse_external_json
        elif lower.endswith((".txt", ".ascii")):
            parse = _parse_external_text
        else:
            continue
        try:
            name, scene = parse(path)
        except Exception as e:
            logger.error("External ascii scene load failed: %s: %s", filename, e)
            continue
        if name in SCENES:
            logger.warning("External ascii scene '%s' overrides builtin", name)
        SCENES[name] = scene
        loaded.append(name)
        logger.info("External ascii scene loaded: %s <- %s", name, filename)
    if loaded:
        normalize()
        for name in loaded:
            if not SCENES[name].get("_external_no_idle") and name not in IDLE_SCENES:
                IDLE_SCENES.append(name)
    return loaded


def load_builtin_scenes():
    """加载随应用分发的内置默认动画，返回加载的场景名列表。

    - exe 模式：默认动画打包在 exe 内（sys._MEIPASS），只读；
    - 源码运行：默认动画就在用户目录里，与用户动画同目录，无需单独加载；
    - 目录不存在时静默跳过（例如旧版 exe 未打包动画资源）。
    """
    if os.path.normcase(BUNDLED_SCENES_DIR) == os.path.normcase(EXTERNAL_SCENES_DIR):
        return []
    if not os.path.isdir(BUNDLED_SCENES_DIR):
        logger.warning("Bundled ascii scenes dir missing: %s", BUNDLED_SCENES_DIR)
        return []
    return load_external_scenes(BUNDLED_SCENES_DIR)


# 启动加载顺序：内置默认动画 → 用户目录（同名文件以用户为准，覆盖默认）
BUILTIN_SCENES = load_builtin_scenes()
EXTERNAL_SCENES = load_external_scenes()

if not SCENES:
    logger.warning("No ascii scenes loaded from %s", EXTERNAL_SCENES_DIR)


# ── 颜色工具 ──────────────────────────────────────────────

def _row_colors(color, n):
    """每行统一用场景色（场景色都是纯黑 #000000，实色即可，不再做渐变）。"""
    return [color] * n


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


# ── 按键 / 鼠标反馈气泡 ───────────────────────────────────
# 全局键盘/鼠标 Hook 触发时，把按下的键 / 点击的按钮渲染成键帽样式小气泡，
# 由 MainWindow 浮在宠物窗口上方展示。下列函数均为纯函数，方便单元测试。

# 功能键 → 键帽显示名（keyboard 库的 event.name 是小写）
_FEEDBACK_KEY_LABELS = {
    "enter": "Enter", "esc": "Esc", "escape": "Esc",
    "space": "Space", "tab": "Tab", "backspace": "Backspace",
    "delete": "Del", "insert": "Ins", "home": "Home", "end": "End",
    "page up": "PgUp", "page down": "PgDn",
    "print screen": "PrtScr", "scroll lock": "ScrLk", "pause": "Pause",
    "caps lock": "CapsLk", "num lock": "NumLk",
    "shift": "Shift", "left shift": "L Shift", "right shift": "R Shift",
    "ctrl": "Ctrl", "control": "Ctrl",
    "left ctrl": "L Ctrl", "right ctrl": "R Ctrl",
    "alt": "Alt", "left alt": "L Alt", "right alt": "R Alt", "alt gr": "AltGr",
    "windows": "Win", "win": "Win",
    "left windows": "L Win", "right windows": "R Win",
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "menu": "Menu",
}

# 键帽内容最多容纳的字符数（超出截断，避免撑出 200px 的宠物窗口）
_FEEDBACK_KEYCAP_MAX = 12


def key_display_label(name):
    """把 keyboard 库的按键名转成键帽上显示的文字。

    - 字母转大写（A、B…），符号/数字原样显示；
    - 常见功能键映射成短名（Enter、Space、L Ctrl…）；
    - 未知按键按单词首字母大写兜底（f1 → F1）。
    """
    if not name:
        return "?"
    key = str(name).strip().lower()
    if key in _FEEDBACK_KEY_LABELS:
        return _FEEDBACK_KEY_LABELS[key]
    if len(key) == 1:
        return key.upper() if key.isalpha() else key
    parts = [w.capitalize() for w in key.split() if w]
    return " ".join(parts) if parts else key


def mouse_display_label(button):
    """把鼠标按钮对象/名字转成键帽文字（LMB / RMB / MMB / X1 / X2）。

    mouse 库的 button 在不同版本里可能是枚举/对象/字符串，统一按 str 匹配。
    """
    text = str(button).lower()
    if "middle" in text:
        return "MMB"
    if "right" in text:
        return "RMB"
    if "left" in text:
        return "LMB"
    if "x2" in text:
        return "X2"
    if "x1" in text:
        return "X1"
    return "Click"


def render_keycap(text):
    """把一行文字渲染成 3 行 ASCII 键帽（等宽字体下对齐不变形）。"""
    label = ((text or "?")).strip()
    if len(label) > _FEEDBACK_KEYCAP_MAX:
        label = label[:_FEEDBACK_KEYCAP_MAX - 1] + "."
    width = len(label) + 2
    border = "+" + "-" * width + "+"
    return "\n".join([
        border,
        "| " + label.ljust(width - 2) + " |",
        border,
    ])
