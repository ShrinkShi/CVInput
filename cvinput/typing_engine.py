import time

from pynput.keyboard import Controller, Key


class TypingEngine:
    KEY_COMBINATION_DELAY = 0.01

    def __init__(self):
        self.controller = Controller()

    def type_text(self, text, interval, stop_event, release_keys, newline_with_shift_enter=True, on_progress=None):
        self._release_trigger_keys(release_keys)
        time.sleep(0.05)
        total = len(text)
        done = 0
        for char in text:
            if stop_event.is_set():
                break
            if char == "\n":
                # Message editors often submit on Enter; this setting types a real Shift+Enter newline instead.
                self.type_newline(newline_with_shift_enter)
            elif char == "\t":
                self.controller.press(Key.tab)
                self.controller.release(Key.tab)
            else:
                self.controller.type(char)
            done += 1
            if on_progress:
                on_progress(done, total)
            time.sleep(interval)

    def type_newline(self, newline_with_shift_enter):
        if not newline_with_shift_enter:
            self.controller.press(Key.enter)
            self.controller.release(Key.enter)
            return

        shift_pressed = False
        enter_pressed = False
        try:
            self.controller.press(Key.shift)
            shift_pressed = True
            time.sleep(self.KEY_COMBINATION_DELAY)
            self.controller.press(Key.enter)
            enter_pressed = True
            self.controller.release(Key.enter)
            enter_pressed = False
            time.sleep(self.KEY_COMBINATION_DELAY)
        finally:
            if enter_pressed:
                self._release_key_safely(Key.enter)
            if shift_pressed:
                self._release_key_safely(Key.shift)

    def _release_trigger_keys(self, release_keys):
        for key in release_keys:
            self._release_key_safely(key)

    def _release_key_safely(self, key):
        try:
            self.controller.release(key)
        except Exception:
            pass
