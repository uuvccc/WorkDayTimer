"""按键/鼠标反馈气泡的纯函数单测：命名映射与键帽渲染。"""
import unittest

from app.ui import ascii_art


class TestKeyDisplayLabel(unittest.TestCase):
    """keyboard 库按键名 → 键帽显示文字。"""

    def test_letters_uppercased(self):
        self.assertEqual(ascii_art.key_display_label("a"), "A")
        self.assertEqual(ascii_art.key_display_label("z"), "Z")
        # 已经是大写也不报错
        self.assertEqual(ascii_art.key_display_label("A"), "A")

    def test_symbols_and_digits_kept(self):
        self.assertEqual(ascii_art.key_display_label("1"), "1")
        self.assertEqual(ascii_art.key_display_label("!"), "!")
        self.assertEqual(ascii_art.key_display_label(";"), ";")

    def test_common_function_keys(self):
        self.assertEqual(ascii_art.key_display_label("enter"), "Enter")
        self.assertEqual(ascii_art.key_display_label("esc"), "Esc")
        self.assertEqual(ascii_art.key_display_label("space"), "Space")
        self.assertEqual(ascii_art.key_display_label("tab"), "Tab")
        self.assertEqual(ascii_art.key_display_label("ctrl"), "Ctrl")
        self.assertEqual(ascii_art.key_display_label("alt"), "Alt")

    def test_modified_keys(self):
        self.assertEqual(ascii_art.key_display_label("left ctrl"), "L Ctrl")
        self.assertEqual(ascii_art.key_display_label("right shift"), "R Shift")
        self.assertEqual(ascii_art.key_display_label("left windows"), "L Win")

    def test_navigation_keys(self):
        self.assertEqual(ascii_art.key_display_label("up"), "Up")
        self.assertEqual(ascii_art.key_display_label("down"), "Down")
        self.assertEqual(ascii_art.key_display_label("page up"), "PgUp")
        self.assertEqual(ascii_art.key_display_label("delete"), "Del")

    def test_unknown_key_fallback(self):
        self.assertEqual(ascii_art.key_display_label("f1"), "F1")
        self.assertEqual(ascii_art.key_display_label("f24"), "F24")

    def test_empty_input(self):
        self.assertEqual(ascii_art.key_display_label(""), "?")
        self.assertEqual(ascii_art.key_display_label(None), "?")


class TestMouseDisplayLabel(unittest.TestCase):
    """鼠标按钮（对象/字符串）→ 键帽显示文字。"""

    def test_left_right_middle(self):
        self.assertEqual(ascii_art.mouse_display_label("left"), "LMB")
        self.assertEqual(ascii_art.mouse_display_label("right"), "RMB")
        self.assertEqual(ascii_art.mouse_display_label("middle"), "MMB")

    def test_side_buttons(self):
        self.assertEqual(ascii_art.mouse_display_label("x1"), "X1")
        self.assertEqual(ascii_art.mouse_display_label("x2"), "X2")

    def test_button_object_repr(self):
        """mouse 库 button 可能是对象（str 形如 Button.left），按 str 匹配。"""

        class _FakeButton:
            def __init__(self, name):
                self._name = name

            def __str__(self):
                return f"Button.{self._name}"

        self.assertEqual(ascii_art.mouse_display_label(_FakeButton("left")), "LMB")
        self.assertEqual(ascii_art.mouse_display_label(_FakeButton("right")), "RMB")
        self.assertEqual(ascii_art.mouse_display_label(_FakeButton("x1")), "X1")

    def test_unknown_fallback(self):
        self.assertEqual(ascii_art.mouse_display_label("wheel"), "Click")


class TestRenderKeycap(unittest.TestCase):
    """键帽渲染：3 行、等宽、内容对齐。"""

    def test_render_single_char(self):
        lines = ascii_art.render_keycap("A").split("\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "+---+")
        self.assertEqual(lines[1], "| A |")
        self.assertEqual(lines[2], "+---+")

    def test_lines_are_equal_width(self):
        for text in ("A", "Enter", "Backspace", "L Ctrl", "!"):
            lines = ascii_art.render_keycap(text).split("\n")
            widths = {len(line) for line in lines}
            self.assertEqual(len(widths), 1, f"{text!r}: lines not equal width: {lines}")
            self.assertTrue(lines[0].startswith("+") and lines[0].endswith("+"))
            self.assertTrue(lines[2].startswith("+") and lines[2].endswith("+"))

    def test_contains_label(self):
        self.assertIn("Space", ascii_art.render_keycap("Space"))

    def test_long_label_truncated(self):
        """超出 12 字符的键名应截断为 11 字符 + '.'，防止撑出窗口。"""
        out = ascii_art.render_keycap("X" * 30)
        self.assertIn("X" * 11 + ".", out)
        self.assertNotIn("X" * 12, out)

    def test_empty_renders_question(self):
        self.assertIn("| ? |", ascii_art.render_keycap(""))


if __name__ == "__main__":
    unittest.main()
