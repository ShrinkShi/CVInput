import time

from pynput.keyboard import Controller, Key


class TypingEngine:
    def __init__(self):
        self.controller = Controller()

    def type_text(self, text, interval, stop_event, release_keys):
        self._release_trigger_keys(release_keys)
        time.sleep(0.05)
        for char in text:
            if stop_event.is_set():
                break
            if char == "\n":
                self.controller.press(Key.enter)
                self.controller.release(Key.enter)
            elif char == "\t":
                self.controller.press(Key.tab)
                self.controller.release(Key.tab)
            else:
                self.controller.type(char)
            time.sleep(interval)

    def _release_trigger_keys(self, release_keys):
        for key in release_keys:
            try:
                self.controller.release(key)
            except Exception:
                pass
