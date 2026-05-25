import threading
import webbrowser

import pyperclip

from .clipboard import ClipboardMonitor
from .config import ConfigStore
from .constants import APP_NAME, DEFAULT_INTERVAL
from .hotkey import HotkeyManager
from .i18n import Translator
from .startup import StartupManager
from .tray import TrayManager
from .typing_engine import TypingEngine
from .ui_ctk import CVInputUI


GITHUB_URL = "https://github.com/ShrinkShi/CVInput"
EMAIL = "1363072460@qq.com"


class CVInputApp:
    def __init__(self):
        self.config_store = ConfigStore()
        self.config = self.config_store.load()
        self.translator = Translator(self.config["language"])

        self.ui = CVInputUI(self, self.config)
        self.hotkey_manager = HotkeyManager()
        self.clipboard_monitor = ClipboardMonitor(self.schedule_clipboard_update)
        self.typing_engine = TypingEngine()
        self.startup_manager = StartupManager()
        self.tray_manager = TrayManager(APP_NAME, self.t, self.request_toggle_window, self.request_exit)
        self.typing_stop_event = threading.Event()
        self.typing_thread = None
        self.exiting = False

        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        self.clipboard_monitor.start()
        self.tray_manager.start()
        self.register_hotkey()

    def t(self, key, **kwargs):
        return self.translator.t(key, **kwargs)

    def run(self):
        self.ui.mainloop()

    def save_config(self):
        self.config_store.save(self.config)

    def register_hotkey(self):
        ok, message = self.hotkey_manager.start(self.config["hotkey"], self.on_hotkey)
        if ok:
            self.ui.set_status(self.t("status.listening_hotkey", hotkey=self.config["hotkey"]), "ready")
        else:
            self.ui.set_status(self.t("status.hotkey_failed"), "error")
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
            self.ui.set_status(self.t("status.text_empty"), "idle")
            return

        self.typing_stop_event.clear()
        self.ui.set_status(self.t("status.typing"), "working")
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
        self.ui.set_status(self.t("status.stopped") if stopped else self.t("status.done"), "ready")
        if not stopped and self.config["clear_after_input"]:
            self.ui.clear_text()

    def on_typing_error(self, message):
        self.ui.set_status(self.t("status.typing_failed", error=message), "error")

    def stop_typing(self):
        self.typing_stop_event.set()
        self.ui.set_status(self.t("status.stopping"), "working")

    def schedule_clipboard_update(self, text):
        self.ui.after(0, lambda value=text: self.update_text_from_clipboard(value))

    def update_text_from_clipboard(self, text):
        if self.ui.is_text_focused():
            return
        self.ui.set_text(text)
        self.ui.set_status(self.t("status.clipboard_chars", count=len(text)), "ready")

    def read_clipboard_now(self):
        try:
            text = pyperclip.paste()
        except Exception as e:
            self.ui.set_status(self.t("status.clipboard_failed", error=e), "error")
            return
        self.update_text_from_clipboard(text if isinstance(text, str) else "")

    def set_clipboard_listener(self, enabled):
        self.config["auto_clipboard"] = bool(enabled)
        self.clipboard_monitor.set_enabled(bool(enabled))
        self.ui.set_clipboard_switch(bool(enabled))
        self.save_config()
        self.ui.set_status(
            self.t("status.clipboard_on") if enabled else self.t("status.clipboard_off"),
            "ready" if enabled else "idle",
        )

    def toggle_always_on_top(self):
        self.set_always_on_top(not bool(self.config["always_on_top"]))

    def set_always_on_top(self, enabled):
        self.config["always_on_top"] = bool(enabled)
        self.ui.set_topmost_value(bool(enabled))
        self.save_config()
        self.ui.set_status(self.t("status.topmost_on") if enabled else self.t("status.topmost_off"), "ready")

    def set_clear_after_input(self, enabled):
        self.config["clear_after_input"] = bool(enabled)
        self.save_config()

    def set_close_to_tray(self, enabled):
        self.config["close_to_tray"] = bool(enabled)
        self.ui.set_close_to_tray_switch(bool(enabled))
        self.save_config()
        self.ui.set_status(
            self.t("status.close_to_tray_on") if enabled else self.t("status.close_to_tray_off"),
            "ready",
        )

    def set_startup_on_boot(self, enabled):
        ok, message = self.startup_manager.set_enabled(bool(enabled))
        if not ok:
            self.ui.set_startup_switch(bool(self.config["startup_on_boot"]))
            self.ui.set_status(self.t("status.startup_failed", error=message), "error")
            return
        self.config["startup_on_boot"] = bool(enabled)
        self.ui.set_startup_switch(bool(enabled))
        self.save_config()
        self.ui.set_status(self.t("status.startup_on") if enabled else self.t("status.startup_off"), "ready")

    def set_opacity(self, value):
        self.config["opacity"] = round(float(value), 2)
        self.ui.set_opacity_value(self.config["opacity"])
        self.save_config()

    def set_language(self, language):
        if language == self.config["language"]:
            return
        self.config["language"] = language
        self.translator.set_language(language)
        self.save_config()
        self.ui.refresh_texts(rebuild_popups=True)
        self.tray_manager.refresh_menu()
        self.ui.set_status(self.t("status.language_changed"), "ready")

    def apply_settings_hotkey(self, hotkey, interval_text):
        try:
            interval = float(interval_text)
        except ValueError:
            interval = DEFAULT_INTERVAL

        interval = min(max(interval, 0.005), 0.5)
        if not hotkey:
            self.ui.show_warning("hotkey", self.t("status.hotkey_empty"))
            return

        old_hotkey = self.config["hotkey"]
        self.config["hotkey"] = hotkey
        self.config["interval"] = interval
        message = self.register_hotkey()
        if message:
            self.config["hotkey"] = old_hotkey
            self.register_hotkey()
            self.ui.show_warning("hotkey", self.t("status.hotkey_failed"))
            return

        self.save_config()
        self.ui.set_status(self.t("status.hotkey_applied", hotkey=hotkey), "ready")

    def open_github(self):
        webbrowser.open(GITHUB_URL)

    def copy_email(self):
        try:
            pyperclip.copy(EMAIL)
        except Exception as e:
            self.ui.set_status(self.t("status.email_copy_failed", error=e), "error")
            return
        self.ui.set_status(self.t("status.email_copied"), "ready")

    def request_toggle_window(self):
        self.ui.after(0, self.toggle_window_visibility)

    def request_exit(self):
        self.ui.after(0, self.exit_app)

    def toggle_window_visibility(self):
        if self.ui.state() == "withdrawn":
            self.show_window()
        else:
            self.hide_window()

    def show_window(self):
        self.ui.deiconify()
        self.ui.after(10, lambda: self.ui.overrideredirect(True))
        self.ui.lift()
        self.ui.focus_force()

    def hide_window(self):
        self.ui.withdraw()

    def close(self):
        if self.config["close_to_tray"] and not self.exiting:
            self.hide_window()
            self.ui.set_status(self.t("status.window_hidden"), "ready")
            return
        self.exit_app()

    def exit_app(self):
        if self.exiting:
            return
        self.exiting = True
        self.typing_stop_event.set()
        self.clipboard_monitor.stop()
        self.hotkey_manager.stop()
        self.tray_manager.stop()
        self.save_config()
        self.ui.destroy()
