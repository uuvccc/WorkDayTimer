import threading

class KeyboardService:
    def __init__(self):
        self._enter_key_callback = None
        self._listener_thread = None
        self._is_running = False

    def set_enter_key_callback(self, callback):
        """Set the callback to be called when Enter key is pressed."""
        self._enter_key_callback = callback

    def start_listening(self):
        """Start listening for keyboard events."""
        if self._is_running:
            return

        self._is_running = True
        self._listener_thread = threading.Thread(target=self._start_listener, daemon=True)
        self._listener_thread.start()

    def _start_listener(self):
        """Start the keyboard listener in a separate thread."""
        try:
            import keyboard

            def on_enter_key(event):
                if event.event_type == keyboard.KEY_DOWN and event.name == 'enter':
                    if self._enter_key_callback:
                        self._enter_key_callback()

            keyboard.hook(on_enter_key)
            keyboard.wait()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"Error in keyboard listener: {e}")

    def stop_listening(self):
        """Stop listening for keyboard events."""
        self._is_running = False
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass

keyboard_service = KeyboardService()