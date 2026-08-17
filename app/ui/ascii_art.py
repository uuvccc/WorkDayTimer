"""ASCII 字符动画场景库与渲染器。

宠物窗口用纯字符（等宽字体）逐帧播放动画。场景定义在 SCENES 里，
每帧是一个字符网格（list[str]），播放前统一 pad 成等宽等高，避免跳动。
渲染支持两种风格：
- 单色：多行纯文本，由 QLabel 的 QSS color 着色；
- rainbow：每行一个颜色（场景色→白色渐变），输出富文本 <span>。

外部导入：把动画文件放进 exe/项目根目录下的 ``ascii_animations/`` 文件夹，
启动时（以及托盘 Reload Animations）会自动加载。支持两种格式：
- ``.json``：结构化定义（name/color/fps/rainbow/frames）
- ``.txt`` / ``.ascii``：``# 键: 值`` 元数据 + ``===`` 帧分隔线的纯文本格式
文件名以 ``_`` 或 ``.`` 开头的文件会被跳过；解析失败的文件记日志并跳过，
不影响启动。格式详见 ``ascii_animations/README.md``。
"""
import html
import json
import os

from app.config.constants import BASE_DIR
from app.utils.logger import logger

# ── 场景库 ────────────────────────────────────────────────
# color   : 单色风格主色（hex）
# fps     : 播放帧率（帧/秒）
# rainbow : 是否逐行渐变着色
# frames  : 每帧为一个 list[str]，行与行对齐（宽度不一致会由 normalize 补齐）
SCENES = {
    "cat": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["      /\\_/\\      ",
             "    _/     \\_    ",
             "   (  o   o  )   ",
             "   (   ^_^   )   ",
             "    \\  \\ /  /    ",
             "     \\_/|_|\\_/    ",
             "       | |       ",
             "      /   \\      "],
            ["      /\\_/\\      ",
             "    _/     \\_    ",
             "   (  -   -  )   ",
             "   (   ^_^   )   ",
             "    \\  \\ /  /    ",
             "     \\_/|_|\\_/    ",
             "       | |       ",
             "      /   \\      "],
            ["      /\\_/\\      ",
             "    _/     \\_    ",
             "   (  o   o  )   ",
             "   (   ^_^   )   ",
             "    \\  \\ /  /    ",
             "     \\_/|_|\\_/    ",
             "       | |       ",
             "      /   \\      "],
            ["      /\\_/\\      ",
             "    _/     \\_    ",
             "   (  ^   ^  )   ",
             "   (   -_-   )   ",
             "    \\  \\ /  /    ",
             "     \\_/|_|\\_/    ",
             "       | |       ",
             "      /   \\      "],
        ],
    },
    "bunny": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["      /\\     /\\     ",
             "     /  \\   /  \\    ",
             "    /    \\_/    \\   ",
             "   (  o     o  )   ",
             "   (    \\_/    )   ",
             "    \\   / \\   /    ",
             "     \\_/   \\_/     ",
             "       |   |       ",
             "      /     \\      "],
            ["      /\\     /\\     ",
             "     /  \\   /  \\    ",
             "    /    \\_/    \\   ",
             "   (  -     -  )   ",
             "   (    \\_/    )   ",
             "    \\   / \\   /    ",
             "     \\_/   \\_/     ",
             "       |   |       ",
             "      /     \\      "],
            ["      /\\     /\\     ",
             "     /  \\   /  \\    ",
             "    /    \\_/    \\   ",
             "   (  ^     ^  )   ",
             "   (    \\_/    )   ",
             "    \\   / \\   /    ",
             "     \\_/   \\_/     ",
             "       |   |       ",
             "      /     \\      "],
        ],
    },
    "penguin": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["    .------.    ",
             "   /  o  o  \\   ",
             "  |   ^_^    |  ",
             "   \\   __   /   ",
             "    '------'    ",
             "    _| | |_     ",
             "   /  | |  \\    ",
             "  /___| |___\\   "],
            ["    .------.    ",
             "   /  -  -  \\   ",
             "  |   ^_^    |  ",
             "   \\   __   /   ",
             "    '------'    ",
             "    _| | |_     ",
             "   /  | |  \\    ",
             "  /___| |___\\   "],
            ["   .------.     ",
             "  /  o  o  \\    ",
             " |   ^_^    |   ",
             "  \\   __   /    ",
             "   '------'     ",
             "   _| | |_      ",
             "  /  | |  \\     ",
             " /___| |___\\    "],
            ["     .------.   ",
             "    /  o  o  \\  ",
             "   |   ^_^    | ",
             "    \\   __   /  ",
             "     '------'   ",
             "     _| | |_    ",
             "    /  | |  \\   ",
             "   /___| |___\\  "],
        ],
    },
    "dog": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["     /\\      /\\    ",
             "    /  \\____/  \\   ",
             "   |  o    o   |  ",
             "   |   (^_^)   |  ",
             "    \\  ____   /   ",
             "     '------'     ",
             "       |  |       ",
             "      /    \\      "],
            ["     /\\      /\\    ",
             "    /  \\____/  \\   ",
             "   |  -    -   |  ",
             "   |   (^_^)   |  ",
             "    \\  ____   /   ",
             "     '------'     ",
             "       |  |       ",
             "      /    \\      "],
            ["    /\\      /\\     ",
             "   /  \\____/  \\    ",
             "  |  o    o   |   ",
             "  |   (^_^)   |   ",
             "   \\  ____   /    ",
             "    '------'      ",
             "      |  |        ",
             "     /    \\       "],
            ["      /\\      /\\  ",
             "     /  \\____/  \\ ",
             "    |  o    o   | ",
             "    |   (^_^)   | ",
             "     \\  ____   /  ",
             "      '------'    ",
             "        |  |      ",
             "       /    \\     "],
        ],
    },
    "robot": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["    [------]    ",
             "   /  o  o  \\   ",
             "  |   ^_^    |  ",
             "   \\  [__]  /   ",
             "    [|    |]    ",
             "     |    |     ",
             "    / \\  / \\    "],
            ["    [------]    ",
             "   /  -  -  \\   ",
             "  |   ^_^    |  ",
             "   \\  [__]  /   ",
             "    [|    |]    ",
             "     |    |     ",
             "    / \\  / \\    "],
            ["    [------]    ",
             "   /  o  o  \\   ",
             "  |   ^_^    |  ",
             "   \\  [__]  /   ",
             "   [|    |]     ",
             "    |    |      ",
             "  / \\  / \\      "],
            ["    [------]    ",
             "   /  o  o  \\   ",
             "  |   ^_^    |  ",
             "   \\  [__]  /   ",
             "     [|    |]   ",
             "      |    |    ",
             "      / \\  / \\  "],
        ],
    },
    "ghost": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["    .------.    ",
             "   /  o  o  \\   ",
             "  |   ^_^    |  ",
             "   \\  ~~~  /    ",
             "  __|     |__   ",
             " |  |  |  |  |  ",
             "    / \\ / \\     "],
            ["    .------.    ",
             "   /  -  -  \\   ",
             "  |   ^_^    |  ",
             "   \\  ~~~  /    ",
             "  __|     |__   ",
             " |  |  |  |  |  ",
             "    / \\ / \\     "],
            ["   .------.     ",
             "  /  o  o  \\    ",
             " |   ^_^    |   ",
             "  \\  ~~~  /     ",
             " __|     |__    ",
             "|  |  |  |  |   ",
             "   / \\ / \\      "],
            ["     .------.   ",
             "    /  o  o  \\  ",
             "   |   ^_^    | ",
             "    \\  ~~~  /   ",
             "  __|     |__   ",
             " |  |  |  |  |  ",
             "    / \\ / \\     "],
        ],
    },
    "fish": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["      o  o      ",
             "   .--------.   ",
             "  /  o    o  \\  ",
             " |    ><(((*>  | ",
             "  \\  ~~~~~~  /   ",
             "   '--------'    "],
            ["     o  o       ",
             "   .--------.   ",
             "  /  -    -  \\  ",
             " |    ><(((*>  | ",
             "  \\  ~~~~~~  /   ",
             "   '--------'    "],
            ["   o  o         ",
             "   .--------.   ",
             "  /  o    o  \\  ",
             " |    ><(((*>  | ",
             "  \\  ~~~~~~  /   ",
             "   '--------'    "],
            ["       o  o     ",
             "   .--------.   ",
             "  /  o    o  \\  ",
             " |    ><(((*>  | ",
             "  \\  ~~~~~~  /   ",
             "   '--------'    "],
        ],
    },
    "bird": {
        "color": "#000000",
        "fps": 4,
        "rainbow": False,
        "frames": [
            ["     /\\  /\\      ",
             "    /  \\/  \\     ",
             "   (  o o  )     ",
             "    \\  ^  /      ",
             "     \\_|_/       ",
             "      / \\        "],
            ["   \\       /     ",
             "    \\  o o  /    ",
             "     \\  ^  /     ",
             "      \\_|_/      ",
             "       / \\       "],
            ["     /\\  /\\      ",
             "    /  \\/  \\     ",
             "   (  - -  )     ",
             "    \\  ^  /      ",
             "     \\_|_/       ",
             "      / \\        "],
        ],
    },
    "chick": {
        "color": "#000000",
        "fps": 4,
        "rainbow": False,
        "frames": [
            ["    .---.     ",
             "   (  o o  )  ",
             "    \\  v  /   ",
             "    /_____\\   ",
             "     / | \\    ",
             "    /  |  \\   "],
            ["  .---.       ",
             " (  o o  )    ",
             "  \\  v  /     ",
             "  /_____\\     ",
             "   / | \\      "],
            ["      .---.   ",
             "     (  o o  )",
             "      \\  v  / ",
             "      /_____\\ ",
             "       / | \\  "],
        ],
    },
    "rocket": {
        "color": "#000000",
        "fps": 4,
        "rainbow": False,
        "frames": [
            ["    /\\         ",
             "   /  \\        ",
             "  |    |       ",
             "  |  o |       ",
             "  |    |       ",
             "  |/  \\|       ",
             "   \\  /        ",
             "    \\/         ",
             "  ******       "],
            ["    /\\         ",
             "   /  \\        ",
             "  |    |       ",
             "  |  - |       ",
             "  |    |       ",
             "  |/  \\|       ",
             "   \\  /        ",
             "    \\/         ",
             "  *  *  *      "],
            ["      /\\       ",
             "     /  \\      ",
             "    |    |     ",
             "    |  o |     ",
             "    |    |     ",
             "    |/  \\|     ",
             "     \\  /      ",
             "      \\/       ",
             "   *****       "],
            ["  /\\           ",
             " /  \\          ",
             "|    |         ",
             "|  o |         ",
             "|    |         ",
             "|/  \\|         ",
             " \\  /          ",
             "  \\/           ",
             " *  *  *       "],
        ],
    },
    "heart": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["  __   __   ",
             " /  \\ /  \\  ",
             "|    V    | ",
             " \\       /  ",
             "  \\     /   ",
             "   \\   /    ",
             "    \\ /     "],
            ["   __   __  ",
             "  /  \\ /  \\ ",
             " |    V    |",
             "  \\       / ",
             "   \\     /  ",
             "    \\   /   ",
             "     \\ /    "],
            ["  __   __   ",
             " /  \\ /  \\  ",
             "|    v    | ",
             " \\       /  ",
             "  \\     /   ",
             "   \\   /    ",
             "    \\ /     "],
        ],
    },
    "alien": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["     \\___/     ",
             "    /  o  \\    ",
             "   |  o o  |   ",
             "   |   ^   |   ",
             "    \\_____/    ",
             "   /  | |  \\   ",
             "      | |      "],
            ["     \\___/     ",
             "    /  -  \\    ",
             "   |  o o  |   ",
             "   |   ^   |   ",
             "    \\_____/    ",
             "   /  | |  \\   ",
             "      | |      "],
            ["   \\_____/     ",
             "   /  o  \\     ",
             "  |  o o  |    ",
             "  |   ^   |    ",
             "   \\_____/     ",
             "  /  | |  \\    ",
             "     | |       "],
        ],
    },
    "octopus": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["    .------.    ",
             "   /  o o  \\   ",
             "  |   ^_^   |  ",
             "   \\  ~~~  /   ",
             "    | | | |    ",
             "   / \\| |/ \\   ",
             "  /  | | |  \\  "],
            ["    .------.    ",
             "   /  - -  \\   ",
             "  |   ^_^   |  ",
             "   \\  ~~~  /   ",
             "    | | | |    ",
             "  / \\| |/ \\   ",
             " /  | | |  \\   "],
            ["    .------.    ",
             "   /  o o  \\   ",
             "  |   ^_^   |  ",
             "   \\  ~~~  /   ",
             "    | | | |    ",
             "   / \\| |/ \\  ",
             "  /  | | |  \\  "],
        ],
    },
    "dino": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["      __      ",
             "     / _)     ",
             "  .-^^^-/ /   ",
             " __/      /   ",
             "<__.|_|-|_|   "],
            ["      __      ",
             "     / _)     ",
             " .-^^^-/ /    ",
             "__/      /    ",
             "<__.|_|-|_|   "],
            ["       __     ",
             "      / _)    ",
             "  .-^^^-/ /   ",
             "  __/      /  ",
             "  <__.|_|-|_| "],
        ],
    },
    "duck": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["     __       ",
             "   <(o )___   ",
             "    ( ._> /   ",
             "     `---'    ",
             "     ~  ~ ~   "],
            ["     __       ",
             "   <(o )___   ",
             "    ( ._> /   ",
             "     `---'    ",
             "    ~ ~  ~    "],
            ["     __       ",
             "   <(- )___   ",
             "    ( ._> /   ",
             "     `---'    ",
             "   ~ ~ ~      "],
        ],
    },
    "panda": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["   .--------.  |",
             "  /  o    o  \\ |",
             " |    ^_^    | ||",
             "  \\  ______ /  ||",
             "   '--------'   ||",
             "     |  |        ",
             "    /    \\       "],
            ["   .--------.  |",
             "  /  -    -  \\ |",
             " |    ^_^    | ||",
             "  \\  ______ /  ||",
             "   '--------'   ||",
             "     |  |        ",
             "    /    \\       "],
            ["   .--------. | ",
             "  /  o    o  \\| ",
             " |    ^_^    | | ",
             "  \\  ______ /  | ",
             "   '--------'   |",
             "     |  |        ",
             "    /    \\       "],
        ],
    },
    "ninja": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["     _^_     ",
             "    /   \\    ",
             "   |  o o  | ",
             "   |   ^   | ",
             "    \\___/    ",
             "     /|\\     ",
             "    / | \\    ",
             "   /  |  \\   "],
            ["     _^_     ",
             "    /   \\    ",
             "   |  - -  | ",
             "   |   ^   | ",
             "    \\___/    ",
             "     /|\\     ",
             "    / | \\    ",
             "   /  |  \\   "],
            ["  _^_        ",
             " /   \\       ",
             "|  o o  |    ",
             "|   ^   |    ",
             " \\___/       ",
             "  /|\\        ",
             " / | \\       ",
             "/  |  \\      "],
            ["        _^_  ",
             "       /   \\ ",
             "      |  o o |",
             "      |   ^  |",
             "       \\___/  ",
             "       /|\\    ",
             "      / | \\   ",
             "     /  |  \\  "],
        ],
    },
    "dancer": {
        "color": "#000000",
        "fps": 4,
        "rainbow": False,
        "frames": [
            ["  (^_^)   ",
             "  (o o)   ",
             "  /| |\\   ",
             "   | |    ",
             "  / \\ / \\ "],
            ["  (^_^)   ",
             "  (- -)   ",
             "  \\| |/   ",
             "   | |    ",
             "  / \\ / \\ "],
            ["  (^_^)   ",
             "  (o o)   ",
             "  /| |\\   ",
             "  _| |_   ",
             "  \\   /   "],
            ["  (^_^)   ",
             "  (o o)   ",
             "  \\| |/   ",
             "  _| |_   ",
             "  /   \\   "],
        ],
    },
    "star": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["     *     ",
             "  *     *  ",
             "   *   *   ",
             "    ***    ",
             "  * *** *  ",
             "   *   *   ",
             "  *     *  ",
             "     *     "],
            ["    ***    ",
             "   * * *   ",
             "  *  *  *  ",
             "     *     ",
             " *  ***  * ",
             "  *  *  *  ",
             "   * * *   ",
             "    ***    "],
        ],
    },
    "sun": {
        "color": "#000000",
        "fps": 3,
        "rainbow": False,
        "frames": [
            ["   \\ | /   ",
             "  -  O  -  ",
             "   / | \\   "],
            ["    \\|/    ",
             "  -  O  -  ",
             "    /|\\    "],
            ["   / | \\   ",
             "  -  O  -  ",
             "   \\ | /   "],
            ["    /|\\    ",
             "  -  O  -  ",
             "    \\|/    "],
        ],
    },
    "fireworks": {
        "color": "#000000",
        "fps": 4,
        "rainbow": True,
        "frames": [
            ["      *      ",
             "     / \\     ",
             "    /   \\    ",
             "   *     *   ",
             "    \\   /    ",
             "     \\ /     ",
             "      *      "],
            ["  *   *   *  ",
             "   * * * *   ",
             "  *  ***  *  ",
             "  *  * *  *  ",
             "     * *     ",
             "    *   *    ",
             "   *     *   "],
            ["   *     *   ",
             "  * *   * *  ",
             " *   * *   * ",
             "*     *     *",
             " *   * *   * ",
             "  * *   * *  ",
             "   *     *   "],
            ["      *      ",
             "    * * *    ",
             "   *  *  *   ",
             "  *   *   *  ",
             "   *  *  *   ",
             "    * * *    ",
             "      *      "],
        ],
    },
    "clock": {
        "color": "#000000",
        "fps": 2,
        "rainbow": True,
        "frames": [
            ["   .---------.   ",
             "  /           \\  ",
             " |   12       |  ",
             " |    ^       |  ",
             " |            |  ",
             " |            |  ",
             "  \\           /  ",
             "   '---------'   "],
            ["   .---------.   ",
             "  /           \\  ",
             " |   12       |  ",
             " |    ->      |  ",
             " |            |  ",
             " |            |  ",
             "  \\           /  ",
             "   '---------'   "],
            ["   .---------.   ",
             "  /           \\  ",
             " |   12       |  ",
             " |    v       |  ",
             " |            |  ",
             " |            |  ",
             "  \\           /  ",
             "   '---------'   "],
            ["   .---------.   ",
             "  /           \\  ",
             " |   12       |  ",
             " |    <-      |  ",
             " |            |  ",
             " |            |  ",
             "  \\           /  ",
             "   '---------'   "],
        ],
    },
    "coffee": {
        "color": "#000000",
        "fps": 2,
        "rainbow": True,
        "frames": [
            ["     ~ ~ ~ ~     ",
             "   .-~~~~~~~-.   ",
             "  /           \\  ",
             " |  c   c   c  | ",
             " |   c    c    | ",
             "  \\           /  ",
             "   '-~~~~~~~-'   "],
            ["      ~ ~ ~      ",
             "   .-~~~~~~~-.   ",
             "  /           \\  ",
             " |  c   c   c  | ",
             " |   c    c    | ",
             "  \\           /  ",
             "   '-~~~~~~~-'   "],
            ["                 ",
             "   .-~~~~~~~-.   ",
             "  /           \\  ",
             " |  c   c   c  | ",
             " |   c    c    | ",
             "  \\           /  ",
             "   '-~~~~~~~-'   "],
            ["     ~ ~ ~ ~     ",
             "   .-~~~~~~~-.   ",
             "  /           \\  ",
             " |  c   c   c  | ",
             " |   c    c    | ",
             "  \\           /  ",
             "   '-~~~~~~~-'   "],
        ],
    },
    "worker": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["   ( o.o )   ",
             "    / | \\    ",
             "   /  |  \\   ",
             "  _/   |   \\_ ",
             "  | |  |  | | ",
             " _|_|__|__|_|_"],
            ["   ( o.o )   ",
             "    \\ | /    ",
             "    \\ | /    ",
             "  __| | |__  ",
             "  | | | | |  ",
             " _|_|_|_|_|_ "],
            ["   ( -.- )   ",
             "    | | |    ",
             "    | | |    ",
             "  __| | |__  ",
             "  | | | | |  ",
             " _|_|_|_|_|_ "],
            ["   ( o.o )   ",
             "    | | |    ",
             "   _| | |_   ",
             "  |_| | |_|  ",
             "  | | | | |  ",
             " _|_|_|_|_|_ "],
        ],
    },
    "sleepy": {
        "color": "#000000",
        "fps": 2,
        "rainbow": False,
        "frames": [
            ["  z  Z  z  ",
             "  ( -_- )  ",
             "   (     )  "],
            ["   Z  z  Z  ",
             "  ( -_- )  ",
             "   (     )  "],
            ["   z  Z     ",
             "  ( -_- )  ",
             "   (     )  "],
            ["      Z  z ",
             "  ( -_- )  ",
             "   (     )  "],
        ],
    },
    "dice": {
        "color": "#000000",
        "fps": 4,
        "rainbow": False,
        "frames": [
            ["  o            ",
             "  .---------.  ",
             "  |         |  ",
             "  |    o    |  ",
             "  |         |  ",
             "  |         |  ",
             "  '---------'  ",
             "            o  "],
            ["        o      ",
             "  .---------.  ",
             "  | o       |  ",
             "  |         |  ",
             "  |         |  ",
             "  |       o |  ",
             "  '---------'  ",
             "   o           "],
            ["  o            ",
             "  .---------.  ",
             "  | o       |  ",
             "  |    o    |  ",
             "  |         |  ",
             "  |       o |  ",
             "  '---------'  ",
             "         o     "],
            ["     o      o  ",
             "  .---------.  ",
             "  | o     o |  ",
             "  |         |  ",
             "  |         |  ",
             "  | o     o |  ",
             "  '---------'  ",
             "  o            "],
        ],
    },
    "celebrate": {
        "color": "#000000",
        "fps": 4,
        "rainbow": True,
        "frames": [
            ["   *     *   ",
             "  \\   |   /  ",
             "   ( o.o )   ",
             "  /   |   \\  ",
             "   *     *   "],
            [" *   *   *   ",
             "   \\ | /     ",
             "  ( ^.^ )    ",
             "   / | \\     ",
             " *   *   *   "],
            ["   *     *   ",
             " *   |     * ",
             "   ( o.o )   ",
             " *   |     * ",
             "   *     *   "],
            ["      *      ",
             "   \\ | /     ",
             "   ( o.o )   ",
             "   / | \\     ",
             "      *      "],
        ],
    },
}

# 待机场景：平时随机轮换这些（替代原图片 60s 随机换图）
IDLE_SCENES = ["cat", "bunny", "coffee", "worker", "dice",
               "penguin", "dog", "robot", "ghost", "fish", "chick", "duck",
               "panda", "dancer", "ninja", "heart", "star", "sun", "fireworks"]


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


# ── 外部场景导入 ─────────────────────────────────────────
# 用户把动画文件放到 exe/项目根目录下的 ascii_animations/ 文件夹即可，
# 应用启动（或托盘 Reload Animations）时自动合并进 SCENES 并参与待机轮换。

# 可写目录下常驻用户动画；冻结（PyInstaller）时就是 exe 旁边的目录
EXTERNAL_SCENES_DIR = os.path.join(BASE_DIR, "ascii_animations")

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
    """扫描外部场景目录，把合法的动画注册进 SCENES 并返回加载的场景名列表。

    - 支持 ``.json`` / ``.txt`` / ``.ascii`` 文件；
    - 文件名以 ``_`` 或 ``.`` 开头的文件跳过（方便放未完成的动画）；
    - 同名场景会覆盖内置场景（以用户文件为准）；
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


# 启动时自动加载用户放入 ascii_animations/ 的外部动画
EXTERNAL_SCENES = load_external_scenes()


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
