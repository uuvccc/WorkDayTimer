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


class TestRenderFrame(unittest.TestCase):
    """渲染输出格式：单色纯文本 vs rainbow 富文本。"""

    def test_plain_scene_returns_plain_text(self):
        scene = ascii_art.SCENES['cat']
        out = ascii_art.render_frame(scene, 0)
        self.assertNotIn('<span', out)
        self.assertNotIn('<br>', out)
        self.assertIn('\n', out)
        self.assertIn('o.o', out)

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
