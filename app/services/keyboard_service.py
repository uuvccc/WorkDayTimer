import threading
from app.utils.logger import logger

class KeyboardService:
    def __init__(self):
        self._enter_key_callback = None
        self._listener_thread = None
        self._is_running = False

    def set_enter_key_callback(self, callback):
        """Set the callback to be called when Enter key is pressed."""
        self._enter_key_callback = callback
        logger.debug(f"Enter key callback set: {callback}")

    def start_listening(self):
        """Start listening for keyboard events."""
        if self._is_running:
            logger.debug("Keyboard listener already running, skip")
            return

        self._is_running = True
        self._listener_thread = threading.Thread(target=self._start_listener, daemon=True)
        self._listener_thread.start()
        logger.info("Keyboard listener started")

    def _start_listener(self):
        """Start the keyboard listener in a separate thread."""
        try:
            import keyboard

            def on_enter_key(event):
                if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
                    logger.debug("Enter key pressed, triggering callback")
                    if self._enter_key_callback:
                        self._enter_key_callback()

            keyboard.hook(on_enter_key)
            logger.debug("Keyboard hook registered with keyboard library")
            keyboard.wait()
        except KeyboardInterrupt:
            logger.debug("Keyboard listener interrupted by KeyboardInterrupt")
        except Exception as e:
            logger.error(f"Error in keyboard listener: {e}", exc_info=True)

    def stop_listening(self):
        """Stop listening for keyboard events."""
        logger.info("Stopping keyboard listener")
        self._is_running = False
        try:
            import keyboard
            keyboard.unhook_all()
            logger.debug("Keyboard hooks unhooked")
        except Exception as e:
            logger.warning(f"Error stopping keyboard listener: {e}")

keyboard_service = KeyboardService()