"""全局输入反馈服务：监听键盘/鼠标 → 回调给 UI。

依赖 ``keyboard`` / ``mouse`` 两个低层 Hook，仅用于 Windows（桌面宠物按键气泡）。
键盘 Hook 复用 keyboard 库（与 keyboard_service 并存，互不影响）；
鼠标 Hook 用 mouse 库。回调在库的内部线程执行，调用方负责切回 GUI 线程
（MainWindow 用 QApplication.postEvent 投递）。

用法：
    feedback_service.start(on_key=cb, on_mouse=cb)
    feedback_service.stop()

出错时只记日志、不影响主流程（Hook 失败 = 无气泡，其他功能照常）。
"""
from app.utils.logger import logger


class FeedbackService:
    """可启停的全局输入事件源：把按键/点击事件以回调形式抛给调用方。"""

    def __init__(self):
        self._on_key = None
        self._on_mouse = None
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    def start(self, on_key=None, on_mouse=None):
        """安装键盘/鼠标 Hook。

        返回 True 表示至少键盘监听已就绪；任一 Hook 安装失败只记日志，
        不影响应用其他功能。
        """
        if self._started:
            logger.debug("Feedback service already started, skip")
            return False
        self._on_key = on_key
        self._on_mouse = on_mouse
        try:
            import keyboard
            keyboard.hook(self._handle_key)
        except Exception as e:
            logger.error(f"Failed to hook keyboard for feedback: {e}", exc_info=True)
        try:
            import mouse
            mouse.hook(self._handle_mouse)
        except Exception as e:
            logger.error(f"Failed to hook mouse for feedback: {e}", exc_info=True)
        self._started = True
        logger.info("Feedback hooks started (keyboard + mouse)")
        return True

    def stop(self):
        """卸载 Hook（按回调精准移除，不影响 keyboard_service 的 Enter 监听）。"""
        if not self._started:
            return
        try:
            import keyboard
            keyboard.unhook(self._handle_key)
        except Exception as e:
            logger.warning(f"Failed to unhook keyboard feedback: {e}")
        try:
            import mouse
            mouse.unhook(self._handle_mouse)
        except Exception as e:
            logger.warning(f"Failed to unhook mouse feedback: {e}")
        self._started = False
        logger.info("Feedback hooks stopped")

    def _handle_key(self, event):
        """keyboard 库回调：只关心按下（含自动重复），忽略抬起。"""
        try:
            import keyboard
            if event.event_type != keyboard.KEY_DOWN:
                return
            name = getattr(event, "name", None)
            if not name:
                return
            if self._on_key:
                self._on_key(name)
        except Exception as e:
            logger.debug(f"Ignored feedback key event: {e}")

    def _handle_mouse(self, event):
        """mouse 库回调：只关心按钮按下/双击，忽略抬起与滚轮。"""
        try:
            import mouse
            if not isinstance(event, mouse.ButtonEvent):
                return
            if event.event_type not in ("down", "double"):
                return
            button = getattr(event, "button", None)
            if button is None:
                return
            if self._on_mouse:
                self._on_mouse(button)
        except Exception as e:
            logger.debug(f"Ignored feedback mouse event: {e}")


feedback_service = FeedbackService()
