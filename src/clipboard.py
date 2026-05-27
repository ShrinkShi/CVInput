import threading
import time

import pyperclip


class ClipboardMonitor:
    def __init__(self, on_text):
        self.on_text = on_text
        self.stop_event = threading.Event()
        self.thread = None
        self.last_text = None
        self.enabled = True

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None

    def set_enabled(self, enabled):
        self.enabled = enabled

    def monitor_loop(self):
        while not self.stop_event.is_set():
            if self.enabled:
                try:
                    text = pyperclip.paste()
                except Exception:
                    time.sleep(0.5)
                    continue

                if isinstance(text, str) and text != self.last_text:
                    self.last_text = text
                    self.on_text(text)
            time.sleep(0.5)
