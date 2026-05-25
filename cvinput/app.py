import threading

import pyperclip

from .clipboard import ClipboardMonitor
from .config import ConfigStore
from .constants import DEFAULT_INTERVAL
from .hotkey import HotkeyManager
from .typing_engine import TypingEngine
from .ui_ctk import CVInputUI


class CVInputApp:
    def __init__(self):
        self.config_store = ConfigStore()
        self.config = self.config_store.load()
        self.ui = CVInputUI(self, self.config)

        self.hotkey_manager = HotkeyManager()
        self.clipboard_monitor = ClipboardMonitor(self.schedule_clipboard_update)
        self.typing_engine = TypingEngine()
        self.typing_stop_event = threading.Event()
        self.typing_thread = None

        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        self.clipboard_monitor.start()
        self.register_hotkey()

    def run(self):
        self.ui.mainloop()

    def save_config(self):
        self.config_store.save(self.config)

    def register_hotkey(self):
        ok, message = self.hotkey_manager.start(self.config["hotkey"], self.on_hotkey)
        if ok:
            self.ui.set_status(f"监听中 · {self.config['hotkey']}", "ready")
        else:
            self.ui.set_status("快捷键注册失败，请更换", "error")
            return message
        return None

    def on_hotkey(self, release_keys):
        self.ui.after(0, lambda keys=release_keys: self.start_typing(keys))

    def start_typing_from_button(self):
        self.start_typing([])

    def start_typing(self, release_keys):
        if self.typing_thread and self.typing_thread.is_alive():
            return
        text = self.ui.get_text()
        if not text:
            self.ui.set_status("文本为空", "idle")
            return

        self.typing_stop_event.clear()
        self.ui.set_status("正在输入", "working")
        self.typing_thread = threading.Thread(
            target=self._typing_worker,
            args=(text, float(self.config["interval"]), release_keys),
            daemon=True,
        )
        self.typing_thread.start()

    def _typing_worker(self, text, interval, release_keys):
        try:
            self.typing_engine.type_text(text, interval, self.typing_stop_event, release_keys)
            stopped = self.typing_stop_event.is_set()
            self.ui.after(0, lambda: self.on_typing_done(stopped))
        except Exception as e:
            self.ui.after(0, lambda message=str(e): self.on_typing_error(message))

    def on_typing_done(self, stopped):
        self.ui.set_status("已停止" if stopped else "输入完成", "ready")
        if not stopped and self.config["clear_after_input"]:
            self.ui.clear_text()

    def on_typing_error(self, message):
        self.ui.set_status(f"输入失败：{message}", "error")

    def stop_typing(self):
        self.typing_stop_event.set()
        self.ui.set_status("正在停止输入", "working")

    def schedule_clipboard_update(self, text):
        self.ui.after(0, lambda value=text: self.update_text_from_clipboard(value))

    def update_text_from_clipboard(self, text):
        if self.ui.is_text_focused():
            return
        self.ui.set_text(text)
        self.ui.set_status(f"剪贴板 {len(text)} 字符", "ready")

    def read_clipboard_now(self):
        try:
            text = pyperclip.paste()
        except Exception as e:
            self.ui.set_status(f"剪贴板读取失败：{e}", "error")
            return
        self.update_text_from_clipboard(text if isinstance(text, str) else "")

    def toggle_clipboard_listener(self):
        enabled = bool(self.ui.listen_switch.get())
        self.set_clipboard_listener_value(enabled)

    def set_clipboard_listener(self):
        enabled = bool(self.ui.clipboard_switch.get())
        self.set_clipboard_listener_value(enabled)

    def set_clipboard_listener_value(self, enabled):
        self.config["auto_clipboard"] = enabled
        self.clipboard_monitor.set_enabled(enabled)
        self.ui.set_clipboard_switch(enabled)
        self.save_config()
        self.ui.set_status("剪贴板监听已开启" if enabled else "剪贴板监听已关闭", "ready" if enabled else "idle")

    def set_always_on_top(self):
        enabled = bool(self.ui.topmost_switch.get())
        self.config["always_on_top"] = enabled
        self.ui.set_topmost_value(enabled)
        self.save_config()
        self.ui.set_status("窗口置顶已开启" if enabled else "窗口置顶已关闭", "ready")

    def set_clear_after_input(self):
        self.config["clear_after_input"] = bool(self.ui.clear_switch.get())
        self.save_config()

    def set_opacity(self, value):
        self.config["opacity"] = round(float(value), 2)
        self.ui.set_opacity_value(self.config["opacity"])
        self.save_config()

    def set_mini_mode(self):
        enabled = bool(self.ui.mini_switch.get())
        self.config["mini_mode"] = enabled
        self.ui.set_mini_mode(enabled)
        self.save_config()
        self.ui.set_status("迷你模式" if enabled else "展开模式", "ready")

    def apply_settings_hotkey(self, hotkey, interval_text, parent):
        try:
            interval = float(interval_text)
        except ValueError:
            interval = DEFAULT_INTERVAL

        interval = min(max(interval, 0.005), 0.5)
        if not hotkey:
            self.ui.show_warning("快捷键无效", "快捷键不能为空。")
            return

        old_hotkey = self.config["hotkey"]
        self.config["hotkey"] = hotkey
        self.config["interval"] = interval
        message = self.register_hotkey()
        if message:
            self.config["hotkey"] = old_hotkey
            self.register_hotkey()
            self.ui.show_warning("快捷键注册失败", "快捷键被占用或注册失败，请更换。")
            return

        self.save_config()
        self.ui.set_status(f"监听中 · {hotkey}", "ready")

    def close(self):
        self.typing_stop_event.set()
        self.clipboard_monitor.stop()
        self.hotkey_manager.stop()
        self.save_config()
        self.ui.destroy()
