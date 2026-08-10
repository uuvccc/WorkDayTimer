import unittest
from unittest.mock import patch

from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QColor, QContextMenuEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication

from app.ui.pet_widget import (
    PET_STATES, STATE_META, MOOD_ANIM,
    resolve_state, format_hms, PetWidget,
)

TOTAL_WORK = 8.5 * 3600  # 默认 8.5h


class TestFormatHms(unittest.TestCase):
    """format_hms：秒数 → 恒 8 字符 HH:MM:SS"""

    def test_zero(self):
        self.assertEqual(format_hms(0), "00:00:00")

    def test_seconds(self):
        self.assertEqual(format_hms(59), "00:00:59")

    def test_minutes(self):
        self.assertEqual(format_hms(60), "00:01:00")

    def test_hour(self):
        self.assertEqual(format_hms(3661), "01:01:01")

    def test_max_day(self):
        self.assertEqual(format_hms(86399), "23:59:59")

    def test_negative(self):
        self.assertEqual(format_hms(-5), "00:00:00")

    def test_float_truncation(self):
        self.assertEqual(format_hms(90.9), "00:01:30")

    def test_always_eight_chars(self):
        for s in (0, 59, 3600, 3661, 86399, 100000):
            self.assertEqual(len(format_hms(s)), 8)


class TestResolveState(unittest.TestCase):
    """resolve_state 状态机各分支"""

    def test_custom_overrides(self):
        self.assertEqual(resolve_state(7200, 50, True, TOTAL_WORK), "custom")

    def test_done_when_remaining_zero(self):
        self.assertEqual(resolve_state(0, 100, False, TOTAL_WORK), "done")

    def test_done_when_remaining_negative(self):
        self.assertEqual(resolve_state(-30, 100, False, TOTAL_WORK), "done")

    def test_idle_before_start(self):
        self.assertEqual(resolve_state(TOTAL_WORK + 100, 0, False, TOTAL_WORK), "idle")

    def test_near_end_by_time(self):
        self.assertEqual(resolve_state(1800, 60, False, TOTAL_WORK), "near_end")

    def test_near_end_by_progress(self):
        self.assertEqual(resolve_state(7200, 90, False, TOTAL_WORK), "near_end")

    def test_near_end_boundary_hour(self):
        # 恰好 1 小时属于 near_end（< 3600 判定）
        self.assertEqual(resolve_state(3599, 50, False, TOTAL_WORK), "near_end")

    def test_working(self):
        self.assertEqual(resolve_state(7200, 50, False, TOTAL_WORK), "working")


class TestStateMeta(unittest.TestCase):
    """STATE_META 与 MOOD_ANIM 元数据自洽"""

    def test_meta_complete_for_all_states(self):
        for state in PET_STATES:
            self.assertIn(state, STATE_META, f"missing STATE_META[{state!r}]")
            meta = STATE_META[state]
            self.assertIsInstance(meta["color"], QColor)
            self.assertTrue(meta["color"].isValid(), f"{state} color invalid")
            self.assertTrue(meta["label"], f"{state} label empty")
            self.assertIn(meta["mood"], MOOD_ANIM, f"mood {meta['mood']!r} missing")

    def test_anim_values_wellformed(self):
        for mood, cfg in MOOD_ANIM.items():
            self.assertGreater(cfg["duration"], 0, f"{mood} duration")
            self.assertEqual(len(cfg["values"]), 3, f"{mood} values")
            self.assertIn(cfg["loop"], (-1, 1), f"{mood} loop")


class TestPetWidgetSmoke(unittest.TestCase):
    """PetWidget 离屏渲染冒烟测试"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.widget = PetWidget()

    @classmethod
    def tearDownClass(cls):
        cls.widget.deleteLater()

    def test_render_all_states(self):
        """5 种状态各渲染一次，不抛异常且产出非空图"""
        for state in PET_STATES:
            with self.subTest(state=state):
                self.widget.set_view(state, 42.0, 7300, "工作中 · 已工作 50%", "tooltip")
                self.widget.resize(200, 200)
                pixmap = self.widget.grab()
                self.assertFalse(pixmap.isNull())

    def test_progress_clamping(self):
        self.widget.set_view("working", 150.0, 0, "")
        self.assertEqual(self.widget._progress, 100.0)
        self.widget.set_view("working", -5.0, -1, "")
        self.assertEqual(self.widget._progress, 0.0)
        self.assertEqual(self.widget._remaining_sec, 0)

    def test_state_change_restarts_animation(self):
        """状态切换应重启动效"""
        from PyQt5.QtCore import QAbstractAnimation

        self.widget.set_view("working", 50.0, 7200, "")
        anim1 = self.widget._anim
        self.assertEqual(anim1.state(), QAbstractAnimation.Running)
        self.assertEqual(anim1.duration(), MOOD_ANIM["bounce"]["duration"])
        self.widget.set_view("done", 100.0, 0, "")
        self.assertEqual(anim1.state(), QAbstractAnimation.Running)
        # 动效配置切换到 celebrate
        self.assertEqual(anim1.duration(), MOOD_ANIM["celebrate"]["duration"])

    def test_context_menu_signal(self):
        """右键应 emit context_menu_requested(globalPos)"""
        captured = []
        self.widget.context_menu_requested.connect(captured.append)
        event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10), QPoint(100, 200))
        self.widget.contextMenuEvent(event)
        self.assertEqual(captured, [QPoint(100, 200)])

    def test_drag_offset_recorded(self):
        """左键按下应记录拖拽偏移"""
        event = QMouseEvent(
            QEvent.MouseButtonPress, QPointF(5, 5), Qt.LeftButton,
            Qt.LeftButton, Qt.NoModifier,
        )
        self.widget.mousePressEvent(event)
        self.assertEqual(self.widget._drag_offset, QPoint(5, 5))


class TestMainWindowWiring(unittest.TestCase):
    """MainWindow → PetWidget 接线集成测试（避免有副作用的系统调用）"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from app.services import time_service as ts, keyboard_service as kb
        from app.config.manager import config_manager as cm
        cls.patches = [
            patch.object(ts, 'is_first_start_of_day', return_value=False),
            patch.object(kb, 'start_listening'),
            patch.object(kb, 'stop_listening'),
            patch('app.main_window.TrayMenu'),
            patch.object(cm, 'should_auto_check', return_value=False),
        ]
        for p in cls.patches:
            p.start()
        from app.main_window import MainWindow
        cls.win = MainWindow(cls.app)

    @classmethod
    def tearDownClass(cls):
        for p in cls.patches:
            p.stop()
        cls.win.deleteLater()
        cls.app.processEvents()

    def test_pet_created_and_fills_window(self):
        self.assertIsInstance(self.win.pet, PetWidget)
        self.assertEqual(self.win.pet.geometry().width(), 200)
        self.assertEqual(self.win.pet.geometry().height(), 200)

    def test_update_pet_display_sets_valid_state(self):
        self.win.update_pet_display()
        self.assertIn(self.win.pet._state, PET_STATES)
        pixmap = self.win.pet.grab()
        self.assertFalse(pixmap.isNull())

    def test_context_menu_signal_connected(self):
        """右键信号 → show_context_menu → tray_menu.menu.exec_"""
        exec_pos = []
        self.win.tray_menu.menu.exec_.side_effect = lambda pos: exec_pos.append(pos)
        self.win.pet.context_menu_requested.emit(QPoint(50, 60))
        self.assertEqual(exec_pos, [QPoint(50, 60)])

    def test_custom_timer_total_recorded(self):
        self.win.start_custom_countdown(5)
        self.assertEqual(self.win._custom_total, 300)


if __name__ == '__main__':
    unittest.main()
