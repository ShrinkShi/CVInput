import copy
import webbrowser

import pyperclip

from ..constants import DEFAULT_CONFIG
from ..debug_logger import export_debug_log, set_debug_enabled


GITHUB_URL = "https://github.com/ShrinkShi/CVInput"
EMAIL = "1363072460@qq.com"


class SettingsController:
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

    def set_debug_mode(self, enabled):
        self.config["debug_mode"] = bool(enabled)
        set_debug_enabled(bool(enabled))
        self.ui.set_debug_switch(bool(enabled))
        self.save_config()
        self.ui.set_status(
            self.t("status.debug_mode_on") if enabled else self.t("status.debug_mode_off"),
            "ready",
        )

    def export_debug_log(self, path):
        try:
            export_debug_log(path, empty_text=self.t("status.debug_log_empty"))
        except Exception as e:
            self.ui.set_status(self.t("status.debug_log_export_failed", error=e), "error")
            return
        self.ui.set_status(self.t("status.debug_log_exported"), "ready")

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
        old_input_hotkey = self.config.get("input_hotkey")
        old_toggle_hotkey = self.config.get("hotkey_toggle_hotkey")
        defaults = copy.deepcopy(DEFAULT_CONFIG)
        self.config.clear()
        self.config.update(defaults)
        if old_startup and not defaults["startup_on_boot"]:
            self.startup_manager.set_enabled(False)
        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        set_debug_enabled(bool(self.config.get("debug_mode", False)))
        self.translator.set_language(self.config["language"])
        self.ensure_multi_slots()
        self.ui.sync_config_controls()
        self.tray_manager.refresh_menu()
        message = self.register_hotkey()
        if message:
            self.config["input_hotkey"] = old_input_hotkey
            self.config["hotkey_toggle_hotkey"] = old_toggle_hotkey
            self.register_hotkey()
            self.ui.show_warning("hotkey", self.t("status.input_hotkey_failed"))
            return
        self.save_config()
        self.ui.refresh_texts(rebuild_popups=True)
        self.ui.set_status(self.t("status.defaults_restored"), "ready")

    def apply_settings_input_hotkey(self, hotkey):
        if not hotkey:
            self.ui.show_warning("hotkey", self.t("status.hotkey_empty"))
            return
        try:
            self.main_hotkey_manager.parse_hotkey(hotkey)
        except ValueError:
            self.ui.show_warning("hotkey", self.t("status.input_hotkey_failed"))
            return

        old_hotkey = self.config["input_hotkey"]
        self.config["input_hotkey"] = hotkey
        message = self.refresh_main_hotkey_registration(force=True)
        if message:
            self.config["input_hotkey"] = old_hotkey
            self.refresh_main_hotkey_registration(force=True)
            self.ui.show_warning("hotkey", self.t("status.input_hotkey_failed"))
            return

        self.save_config()
        self.ui.set_status(self.t("status.hotkey_applied", hotkey=hotkey), "ready")

    def apply_settings_hotkey(self, hotkey):
        self.apply_settings_input_hotkey(hotkey)

    def apply_settings_hotkey_toggle_hotkey(self, hotkey):
        if not hotkey:
            self.ui.show_warning("hotkey", self.t("status.hotkey_empty"))
            return
        try:
            self.toggle_hotkey_manager.parse_hotkey(hotkey)
        except ValueError:
            self.ui.show_warning("hotkey", self.t("status.hotkey_toggle_failed"))
            return

        old_hotkey = self.config["hotkey_toggle_hotkey"]
        self.config["hotkey_toggle_hotkey"] = hotkey
        message = self.refresh_toggle_hotkey_registration(force=True)
        if message:
            self.config["hotkey_toggle_hotkey"] = old_hotkey
            self.refresh_toggle_hotkey_registration(force=True)
            self.ui.show_warning("hotkey", self.t("status.hotkey_toggle_failed"))
            return

        self.save_config()
        self.ui.set_status(self.t("status.hotkey_toggle_applied", hotkey=hotkey), "ready")

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
