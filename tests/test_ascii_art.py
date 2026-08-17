import json
import os
import tempfile
import unittest

from app.ui import ascii_art


class TestSceneData(unittest.TestCase):
    """场景数据完整性：结构、网格、fps、待机清单。"""

    def test_scenes_non_empty(self):
        self.assertTrue(ascii_art.SCENES)
        self.assertTrue(ascii_art.IDLE_SCENES)

    def test_scene_structure(self):
        for name, scene in ascii_art.SCENES.items():
            self.assertIn('frames', scene, f"{name} missing frames")
            self.assertIn('color', scene, f"{name} missing color")
            self.assertIn('fps', scene, f"{name} missing fps")
            self.assertTrue(scene['frames'], f"{name} has no frames")
            self.assertRegex(scene['color'], r'^#[0-9A-Fa-f]{6}$',
                             f"{name} color must be #RRGGBB")

    def test_fps_positive(self):
        for name, scene in ascii_art.SCENES.items():
            self.assertGreater(scene['fps'], 0, f"{name} fps must be positive")

    def test_frames_uniform_grid(self):
        """所有帧 pad 成统一网格：同场景每帧等高、每帧每行等宽，播放不跳动。"""
        for name, scene in ascii_art.SCENES.items():
            frames = scene['frames']
            height = len(frames[0])
            width = max(len(row) for row in frames[0])
            for idx, frame in enumerate(frames):
                self.assertEqual(len(frame), height,
                                 f"{name} frame {idx}: height mismatch "
                                 f"({len(frame)} vs {height})")
                for row in frame:
                    self.assertEqual(len(row), width,
                                     f"{name} frame {idx}: row width mismatch "
                                     f"({len(row)} vs {width})")

    def test_idle_scenes_are_valid(self):
        for name in ascii_art.IDLE_SCENES:
            self.assertIn(name, ascii_art.SCENES, f"idle scene '{name}' not in SCENES")

    def test_render_any_frame_index(self):
        """索引越界时应取模回绕，不会抛异常。"""
        for name, scene in ascii_art.SCENES.items():
            out = ascii_art.render_frame(scene, 999)
            self.assertTrue(out, f"{name} render index 999 returned empty")


class TestExternalScenes(unittest.TestCase):
    """外部动画导入：JSON / 文本解析、目录扫描、注册与轮换。"""

    def _write(self, directory, filename, content):
        path = os.path.join(directory, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _cleanup(self, name):
        """移除测试期间注册进全局 SCENES / IDLE_SCENES 的外部场景。"""
        ascii_art.SCENES.pop(name, None)
        if name in ascii_art.IDLE_SCENES:
            ascii_art.IDLE_SCENES.remove(name)

    def test_parse_external_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "wow.json", json.dumps({
                "name": "wow",
                "color": "#FF0000",
                "fps": 4,
                "rainbow": True,
                "frames": [["a", "bb"], ["c", "dd"]],
            }))
            name, scene = ascii_art._parse_external_json(path)
            self.assertEqual(name, "wow")
            self.assertEqual(scene["color"], "#FF0000")
            self.assertEqual(scene["fps"], 4)
            self.assertTrue(scene["rainbow"])
            self.assertEqual(scene["frames"], [["a", "bb"], ["c", "dd"]])

    def test_parse_external_json_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "no_name.json", json.dumps({
                "frames": ["hello", "world"],
            }))
            name, scene = ascii_art._parse_external_json(path)
            self.assertEqual(name, "no_name")
            self.assertEqual(scene["color"], "#000000")
            self.assertEqual(scene["fps"], 2)
            self.assertFalse(scene["rainbow"])
            self.assertEqual(len(scene["frames"]), 2)
            self.assertEqual(scene["frames"][0], ["hello"])

    def test_parse_external_json_invalid_raises(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "bad.json", '{"foo": 1}')
            with self.assertRaises(ValueError):
                ascii_art._parse_external_json(path)

    def test_parse_external_json_idle_false(self):
        """JSON 也支持 idle: false，解析后标记不参与待机轮换。"""
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "quiet.json", json.dumps({
                "idle": False,
                "frames": [["a"]],
            }))
            name, scene = ascii_art._parse_external_json(path)
            self.assertEqual(name, "quiet")
            self.assertTrue(scene.get("_external_no_idle"))

    def test_parse_external_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "pet.txt", "\n".join([
                "# name: my_pet",
                "# color: #00FF00",
                "# fps: 5",
                "# rainbow: true",
                "# idle: false",
                "===",
                "line1a",
                "line1b",
                "===",
                "line2a",
                "line2b",
            ]))
            name, scene = ascii_art._parse_external_text(path)
            self.assertEqual(name, "my_pet")
            self.assertEqual(scene["color"], "#00FF00")
            self.assertEqual(scene["fps"], 5)
            self.assertTrue(scene["rainbow"])
            self.assertTrue(scene.get("_external_no_idle"))
            self.assertEqual(len(scene["frames"]), 2)
            self.assertEqual(scene["frames"][0], ["line1a", "line1b"])

    def test_parse_external_text_single_frame(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write(d, "single.txt", "hello\nworld\n")
            name, scene = ascii_art._parse_external_text(path)
            self.assertEqual(scene["frames"], [["hello", "world"]])

    def test_load_external_scenes_registers_and_skips(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "pet.txt", "===\na\n===\nb\n")
            self._write(d, "_draft.txt", "not\nloaded\n")
            self._write(d, ".hidden.json", '{"frames": [["x"]]}')
            self._write(d, "note.md", "ignore me")
            names = ascii_art.load_external_scenes(directory=d)
            try:
                self.assertEqual(names, ["pet"])
                self.assertIn("pet", ascii_art.SCENES)
                self.assertIn("pet", ascii_art.IDLE_SCENES)
                self.assertNotIn("_draft", ascii_art.SCENES)
                self.assertNotIn("note", ascii_art.SCENES)
            finally:
                self._cleanup("pet")

    def test_load_external_scene_idle_false_not_in_rotation(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "quiet.txt", "# idle: false\n===\na\n===\nb\n")
            names = ascii_art.load_external_scenes(directory=d)
            try:
                self.assertEqual(names, ["quiet"])
                self.assertIn("quiet", ascii_art.SCENES)
                self.assertNotIn("quiet", ascii_art.IDLE_SCENES)
            finally:
                self._cleanup("quiet")

    def test_external_scene_normalized_and_renderable(self):
        """外部场景注册后应像内置场景一样被 normalize 补齐网格并可渲染。"""
        with tempfile.TemporaryDirectory() as d:
            self._write(d, "grid.json", json.dumps({
                "frames": [["a", "bb"], ["ccc"]],
            }))
            names = ascii_art.load_external_scenes(directory=d)
            try:
                self.assertEqual(names, ["grid"])
                scene = ascii_art.SCENES["grid"]
                self.assertEqual([len(f) for f in scene["frames"]], [2, 2])
                self.assertEqual(scene["frames"][1], ["ccc", "   "])
                self.assertEqual(ascii_art.render_frame(scene, 0), "a  \nbb ")
            finally:
                self._cleanup("grid")


class TestRenderFrame(unittest.TestCase):
    """渲染输出格式：单色纯文本 vs rainbow 富文本。"""

    def test_plain_scene_returns_plain_text(self):
        scene = ascii_art.SCENES['cat']
        out = ascii_art.render_frame(scene, 0)
        self.assertNotIn('<span', out)
        self.assertNotIn('<br>', out)
        self.assertIn('\n', out)
        # 2x 网格后猫脸变成 `(  o   o  )`（原来是 `( o.o )`）
        self.assertIn('  o   o  ', out)

    def test_rainbow_scene_uses_spans(self):
        scene = ascii_art.SCENES['clock']
        out = ascii_art.render_frame(scene, 0)
        self.assertIn('<span style="color:', out)
        self.assertIn('<br>', out)

    def test_rainbow_escapes_art_angle_brackets(self):
        """rainbow 场景帧里的 '<' '>' 必须被 html 转义，避免被 Qt 当标签。"""
        scene = ascii_art.SCENES['clock']
        out = ascii_art.render_frame(scene, 1)  # 该帧表针是 '->'，含裸 '>'
        self.assertIn('&gt;', out)

    def test_rainbow_output_well_formed(self):
        """rainbow 输出 <span> 与 </span> 数量应匹配。"""
        for name, scene in ascii_art.SCENES.items():
            if not scene.get('rainbow'):
                continue
            for i in range(len(scene['frames'])):
                out = ascii_art.render_frame(scene, i)
                self.assertEqual(out.count('<span'), out.count('</span>'),
                                 f"{name} frame {i}: unbalanced span tags")

    def test_row_colors_count(self):
        colors = ascii_art._row_colors('#FF9A8B', 5)
        self.assertEqual(len(colors), 5)


if __name__ == '__main__':
    unittest.main()
