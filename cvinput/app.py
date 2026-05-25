import copy
import threading
import webbrowser

import pyperclip

from .clipboard import ClipboardMonitor
from .config import ConfigStore
from .constants import APP_NAME, DEFAULT_CONFIG, DEFAULT_INTERVAL_MS
from .hotkey import HotkeyManager
from .ime import maybe_toggle_ime_before_typing, restore_ime_after_typing
from .i18n import Translator
from .startup import StartupManager
from .tray import TrayManager
from .typing_engine import TypingEngine
from .ui_ctk import CVInputUI


GITHUB_URL = "https://github.com/ShrinkShi/CVInput"
EMAIL = "1363072460@qq.com"
SLOT_HOTKEYS = ["Alt+1", "Alt+2", "Alt+3", "Alt+4", "Alt+5", "Alt+6", "Alt+7", "Alt+8", "Alt+9", "Alt+0"]


class CVInputApp:
    def __init__(self):
        self.config_store = ConfigStore()
        self.config = self.config_store.load()
        self.ensure_multi_slots()
        self.translator = Translator(self.config["language"])

        self.ui = CVInputUI(self, self.config)
        self.main_hotkey_manager = HotkeyManager()
        self.slot_hotkey_manager = HotkeyManager(base_id=100)
        self.main_hotkey_registered = False
        self.registered_main_hotkey = None
        self.slot_hotkeys_active = False
        self.clipboard_monitor = ClipboardMonitor(self.schedule_clipboard_update)
        self.typing_engine = TypingEngine()
        self.startup_manager = StartupManager()
        self.tray_manager = TrayManager(APP_NAME, self.t, self.request_activate_window, self.request_toggle_window, self.request_exit)
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
        message = self.refresh_main_hotkey_registration(force=True)
        self.refresh_slot_hotkey_registration(force=True)
        return message

    def refresh_main_hotkey_registration(self, force=False, show_status=True):
        hotkey = str(self.config["hotkey"])
        clipboard_empty = not self.ui.get_text().strip()
        should_release = bool(self.config["disable_hotkey_when_clipboard_empty"]) and clipboard_empty
        if should_release:
            if self.main_hotkey_registered or force:
                self.main_hotkey_manager.stop()
            self.main_hotkey_registered = False
            self.registered_main_hotkey = None
            if show_status:
                self.ui.set_status(self.t("status.hotkey_released_empty", hotkey=hotkey), "idle")
            return None

        if not force and self.main_hotkey_registered and self.registered_main_hotkey == hotkey:
            if show_status:
                self.ui.set_status(self.t("status.hotkey_registered", hotkey=hotkey), "ready")
            return None

        self.main_hotkey_manager.stop()
        registered, failures = self.main_hotkey_manager.start_all({"main": hotkey}, self.on_hotkey)
        if "main" not in registered:
            self.main_hotkey_registered = False
            self.registered_main_hotkey = None
            if show_status:
                self.ui.set_status(self.t("status.hotkey_failed"), "error")
            return failures.get("main", self.t("status.hotkey_failed"))

        self.main_hotkey_registered = True
        self.registered_main_hotkey = hotkey
        if show_status:
            self.ui.set_status(self.t("status.hotkey_registered", hotkey=hotkey), "ready")
        return None

    def refresh_slot_hotkey_registration(self, force=False):
        if not self.config["multi_slot_enabled"]:
            self.slot_hotkey_manager.stop()
            self.slot_hotkeys_active = False
            return
        if self.slot_hotkeys_active and not force:
            return
        hotkeys = {f"slot_{index}": hotkey for index, hotkey in enumerate(SLOT_HOTKEYS)}
        registered, failures = self.slot_hotkey_manager.start_all(hotkeys, self.on_hotkey)
        self.slot_hotkeys_active = bool(registered)
        slot_failures = [self.slot_label(action) for action in failures if action.startswith("slot_")]
        if slot_failures:
            self.ui.set_status(self.t("status.slot_hotkey_failed", slots=", ".join(slot_failures)), "error")

    def on_hotkey(self, action, release_keys):
        self.ui.after(0, lambda hotkey_action=action, keys=release_keys: self.handle_hotkey(hotkey_action, keys))

    def handle_hotkey(self, action, release_keys):
        if action == "main":
            self.start_typing_from_hotkey(release_keys)
            return
        if action.startswith("slot_"):
            self.start_typing_from_slot(int(action.split("_", 1)[1]), release_keys)

    def start_typing_from_hotkey(self, release_keys):
        if self.config["disable_hotkey_when_clipboard_empty"] and not self.ui.get_text().strip():
            self.refresh_main_hotkey_registration(force=True)
            return
        self.start_typing(release_keys)

    def start_typing_from_slot(self, index, release_keys):
        slots = self.config.get("multi_slots", [])
        text = slots[index] if 0 <= index < len(slots) else ""
        if not text:
            self.ui.set_status(self.t("status.slot_empty", slot=self.slot_label(f"slot_{index}")), "idle")
            return
        self.start_typing(release_keys, text=text)

    def start_typing_from_button(self):
        self.start_typing([])

    def start_typing(self, release_keys, text=None):
        if self.typing_thread and self.typing_thread.is_alive():
            return
        if text is None:
            text = self.ui.get_text()
        if not text:
            self.ui.set_status(self.t("status.text_empty"), "idle")
            return

        self.typing_stop_event.clear()
        self.ui.reset_input_progress()
        self.ui.set_status(self.t("status.typing"), "working")
        self.typing_thread = threading.Thread(
            target=self._typing_worker,
            args=(text, self.input_interval_seconds(), release_keys),
            daemon=True,
        )
        self.typing_thread.start()

    def input_interval_seconds(self):
        interval_ms = DEFAULT_INTERVAL_MS
        if self.config.get("custom_interval_enabled", False):
            try:
                interval_ms = float(self.config.get("interval_ms", DEFAULT_INTERVAL_MS))
            except (TypeError, ValueError):
                interval_ms = DEFAULT_INTERVAL_MS
        return interval_ms / 1000

    def _typing_worker(self, text, interval, release_keys):
        should_restore_ime = False
        try:
            should_restore_ime = maybe_toggle_ime_before_typing(self.config)
            progress_callback = lambda done, total: self.ui.after(
                0,
                lambda current=done, count=total: self.ui.set_input_progress(current, count),
            )
            self.typing_engine.type_text(
                text,
                interval,
                self.typing_stop_event,
                release_keys,
                bool(self.config["newline_with_shift_enter"]),
                progress_callback,
            )
            stopped = self.typing_stop_event.is_set()
            self.ui.after(0, lambda: self.on_typing_done(stopped))
        except Exception as e:
            self.ui.after(0, lambda message=str(e): self.on_typing_error(message))
        finally:
            restore_ime_after_typing(should_restore_ime)

    def on_typing_done(self, stopped):
        self.ui.set_status(self.t("status.stopped") if stopped else self.t("status.done"), "ready")
        if not stopped and self.config["clear_after_input"]:
            self.ui.clear_text()
            self.refresh_main_hotkey_registration()

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
        self.refresh_main_hotkey_registration()

    def on_main_text_changed(self):
        self.refresh_main_hotkey_registration()

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

    def set_disable_hotkey_when_clipboard_empty(self, enabled):
        self.config["disable_hotkey_when_clipboard_empty"] = bool(enabled)
        self.ui.set_disable_empty_switch(bool(enabled))
        self.save_config()
        self.refresh_main_hotkey_registration(force=True)

    def set_toggle_ime_with_shift(self, enabled):
        self.config["toggle_ime_with_shift"] = bool(enabled)
        self.ui.set_ime_switch(bool(enabled))
        self.save_config()

    def set_newline_with_shift_enter(self, enabled):
        self.config["newline_with_shift_enter"] = bool(enabled)
        self.ui.set_newline_switch(bool(enabled))
        self.save_config()

    def set_custom_interval_enabled(self, enabled):
        self.config["custom_interval_enabled"] = bool(enabled)
        self.ui.set_custom_interval_switch(bool(enabled))
        self.ui.set_interval_controls_visible(bool(enabled))
        self.save_config()

    def set_remember_settings(self, enabled):
        self.config["remember_settings"] = bool(enabled)
        self.ui.set_remember_settings_switch(bool(enabled))
        self.save_config()

    def set_close_popup_on_blur(self, enabled):
        self.config["close_popup_on_blur"] = bool(enabled)
        self.ui.set_close_popup_on_blur_switch(bool(enabled))
        self.ui.refresh_popup_blur_behavior()
        self.save_config()

    def set_multi_slot_enabled(self, enabled):
        self.config["multi_slot_enabled"] = bool(enabled)
        self.ensure_multi_slots()
        self.ui.set_multi_slot_visible(bool(enabled))
        self.save_config()
        self.refresh_slot_hotkey_registration(force=True)

    def update_multi_slot(self, index, text):
        self.ensure_multi_slots()
        if 0 <= index < len(self.config["multi_slots"]):
            self.config["multi_slots"][index] = text
            self.save_config()

    def ensure_multi_slots(self):
        slots = self.config.get("multi_slots")
        if not isinstance(slots, list):
            slots = []
        normalized = [str(slots[index]) if index < len(slots) else "" for index in range(10)]
        self.config["multi_slots"] = normalized

    def slot_label(self, action):
        if not action.startswith("slot_"):
            return action
        index = int(action.split("_", 1)[1])
        return SLOT_HOTKEYS[index] if 0 <= index < len(SLOT_HOTKEYS) else action

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

    def restore_default_settings(self):
        old_startup = bool(self.config.get("startup_on_boot"))
        old_hotkey = self.config.get("hotkey")
        defaults = copy.deepcopy(DEFAULT_CONFIG)
        self.config.clear()
        self.config.update(defaults)
        if old_startup and not defaults["startup_on_boot"]:
            self.startup_manager.set_enabled(False)
        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        self.translator.set_language(self.config["language"])
        self.ensure_multi_slots()
        self.ui.sync_config_controls()
        self.tray_manager.refresh_menu()
        message = self.register_hotkey()
        if message:
            self.config["hotkey"] = old_hotkey
            self.register_hotkey()
            self.ui.show_warning("hotkey", self.t("status.hotkey_failed"))
            return
        self.save_config()
        self.ui.refresh_texts(rebuild_popups=True)
        self.ui.set_status(self.t("status.defaults_restored"), "ready")

    def apply_settings_hotkey(self, hotkey):
        if not hotkey:
            self.ui.show_warning("hotkey", self.t("status.hotkey_empty"))
            return
        try:
            self.main_hotkey_manager.parse_hotkey(hotkey)
        except ValueError:
            self.ui.show_warning("hotkey", self.t("status.hotkey_failed"))
            return

        old_hotkey = self.config["hotkey"]
        self.config["hotkey"] = hotkey
        message = self.refresh_main_hotkey_registration(force=True)
        if message:
            self.config["hotkey"] = old_hotkey
            self.refresh_main_hotkey_registration(force=True)
            self.ui.show_warning("hotkey", self.t("status.hotkey_failed"))
            return

        self.save_config()
        self.ui.set_status(self.t("status.hotkey_applied", hotkey=hotkey), "ready")

    def apply_settings_interval(self, interval_text):
        try:
            interval_ms = float(interval_text)
        except ValueError:
            self.ui.show_warning("interval", self.t("status.interval_invalid"))
            return
        if not 0.1 <= interval_ms <= 10000:
            self.ui.show_warning("interval", self.t("status.interval_invalid"))
            return
        self.config["interval_ms"] = round(interval_ms, 3)
        self.save_config()
        self.ui.sync_config_controls()
        self.ui.set_status(self.t("status.interval_updated", interval=self.config["interval_ms"]), "ready")

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

    def request_activate_window(self):
        self.ui.after(0, self.activate_window_from_tray)

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

    def activate_window_from_tray(self):
        if self.ui.state() == "withdrawn":
            self.show_window()
            return
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
        self.main_hotkey_manager.stop()
        self.slot_hotkey_manager.stop()
        self.tray_manager.stop()
        self.save_config()
        self.ui.destroy()
