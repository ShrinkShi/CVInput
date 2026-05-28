import copy
import webbrowser

import pyperclip

from ..constants import (
    DEFAULT_CONFIG,
    DEFAULT_INPUT_ENCODING,
    DEFAULT_OUTPUT_ENCODING,
    DEFAULT_SINGLE_LINE_REPLACEMENT,
    DEFAULT_TYPING_MODE,
    TYPING_INTERVAL_MODE_CUSTOM_INTERVAL,
    TYPING_INTERVAL_MODE_DEFAULT,
    TYPING_INTERVAL_MODES,
    INPUT_ENCODINGS,
    NEWLINE_METHOD_VERSION,
    NEWLINE_METHODS,
    OUTPUT_ENCODINGS,
    SINGLE_LINE_REPLACEMENTS,
    TYPING_MODES,
)
from ..debug_logger import (
    CATEGORY_IME,
    CATEGORY_NEWLINE_BEHAVIOR,
    CATEGORY_WINDOW_POSITION,
    clear_debug_log,
    debug_log,
    export_debug_log,
    get_debug_log_count,
    set_category_enabled,
    set_developer_mode,
)


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

    def set_typing_mode(self, mode):
        self.apply_input_mode_settings(mode, self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT))

    def set_single_line_replacement(self, replacement):
        self.apply_input_mode_settings(self.current_input_mode(), replacement)

    def apply_input_mode_settings(self, mode, replacement):
        if mode not in TYPING_MODES:
            return
        if replacement not in SINGLE_LINE_REPLACEMENTS:
            return
        if mode != self.current_input_mode():
            self.clear_split_queue()
        self.config["input_mode"] = mode
        self.config["typing_mode"] = mode
        self.config["single_line_replacement"] = replacement
        self.ui.set_typing_mode_value(mode)
        self.ui.set_single_line_replacement_value(replacement)
        self.ui.set_single_line_replacement_visible(mode)
        self.save_config()
        self.refresh_main_hotkey_registration(force=True)
        self.apply_mode_to_raw_text()
        print(f"[INPUT_MODE] applied mode={mode} replacement={replacement}", flush=True)
        debug_log("NEWLINE_BEHAVIOR", "input_mode_applied", mode=mode, replacement=replacement)
        self.ui.set_status(self.t("status.mode_applied"), "ready")

    def current_input_mode(self):
        return self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE))

    def set_text_encodings(self, input_encoding, output_encoding):
        if input_encoding not in INPUT_ENCODINGS:
            return
        if output_encoding not in OUTPUT_ENCODINGS:
            return
        self.config["input_encoding"] = input_encoding
        self.config["output_encoding"] = output_encoding
        self.ui.set_encoding_values(input_encoding, output_encoding)
        self.save_config()
        self.ui.set_status(self.t("status.encoding_applied"), "ready")

    def set_newline_shift_enter_method(self, method):
        if method not in NEWLINE_METHODS:
            return
        self.config["newline_shift_enter_method"] = method
        self.config["newline_shift_enter_method_version"] = NEWLINE_METHOD_VERSION
        self.ui.set_newline_method_value(method)
        self.save_config()
        self.ui.set_status(self.t("status.newline_method_updated"), "ready")

    def set_custom_interval_enabled(self, enabled):
        mode = TYPING_INTERVAL_MODE_CUSTOM_INTERVAL if enabled else TYPING_INTERVAL_MODE_DEFAULT
        self.set_typing_interval_mode(mode)

    def set_typing_interval_mode(self, mode):
        if mode not in TYPING_INTERVAL_MODES:
            return
        self.config["typing_interval_mode"] = mode
        self.config["custom_interval_enabled"] = mode == TYPING_INTERVAL_MODE_CUSTOM_INTERVAL
        self.ui.set_typing_interval_mode_value(mode)
        self.ui.set_interval_controls_visible(mode)
        self.save_config()
        self.ui.set_status(self.t("status.typing_interval_mode_applied"), "ready")

    def set_remember_settings(self, enabled):
        self.config["remember_settings"] = bool(enabled)
        self.ui.set_remember_settings_switch(bool(enabled))
        self.save_config()

    def set_close_popup_on_blur(self, enabled):
        self.config["close_popup_on_blur"] = bool(enabled)
        self.ui.set_close_popup_on_blur_switch(bool(enabled))
        self.ui.refresh_popup_blur_behavior()
        self.save_config()

    def set_developer_mode(self, enabled):
        self.config["developer_mode"] = bool(enabled)
        set_developer_mode(bool(enabled))
        self.ui.set_developer_switch(bool(enabled))
        self.ui.refresh_developer_debug_visibility()
        self.save_config()
        self.ui.set_status(
            self.t("status.developer_mode_on") if enabled else self.t("status.developer_mode_off"),
            "ready",
        )

    def set_debug_window_position(self, enabled):
        self.config["debug_window_position"] = bool(enabled)
        set_category_enabled(CATEGORY_WINDOW_POSITION, bool(enabled))
        self.ui.set_debug_window_position_switch(bool(enabled))
        self.save_config()
        self.ui.update_developer_log_count()

    def set_debug_newline_behavior(self, enabled):
        self.config["debug_newline_behavior"] = bool(enabled)
        set_category_enabled(CATEGORY_NEWLINE_BEHAVIOR, bool(enabled))
        set_category_enabled(CATEGORY_IME, bool(enabled))
        self.ui.set_debug_newline_behavior_switch(bool(enabled))
        self.save_config()
        self.ui.update_developer_log_count()

    def export_debug_log(self, path):
        try:
            export_debug_log(
                path,
                empty_text=self.t("status.debug_log_empty"),
                encoding=self.config.get("output_encoding", DEFAULT_OUTPUT_ENCODING),
            )
        except Exception as e:
            self.ui.set_status(self.t("status.debug_log_export_failed", error=e), "error")
            return
        self.ui.set_status(self.t("status.debug_log_exported"), "ready")

    def clear_debug_log_from_settings(self):
        clear_debug_log()
        self.ui.update_developer_log_count()
        self.ui.set_status(self.t("status.debug_log_cleared"), "ready")

    def debug_log_count(self):
        return get_debug_log_count()

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
        old_stop_hotkey = self.config.get("stop_typing_hotkey", self.config.get("input_hotkey"))
        old_toggle_hotkey = self.config.get("hotkey_toggle_hotkey")
        defaults = copy.deepcopy(DEFAULT_CONFIG)
        self.config.clear()
        self.config.update(defaults)
        self.clear_split_queue()
        if old_startup and not defaults["startup_on_boot"]:
            self.startup_manager.set_enabled(False)
        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        set_developer_mode(bool(self.config.get("developer_mode", False)))
        set_category_enabled(CATEGORY_WINDOW_POSITION, bool(self.config.get("debug_window_position", False)))
        set_category_enabled(CATEGORY_NEWLINE_BEHAVIOR, bool(self.config.get("debug_newline_behavior", False)))
        set_category_enabled(CATEGORY_IME, bool(self.config.get("debug_newline_behavior", False)))
        self.translator.set_language(self.config["language"])
        self.ensure_multi_slots()
        self.ui.sync_config_controls()
        self.tray_manager.refresh_menu()
        message = self.register_hotkey()
        if message:
            self.config["input_hotkey"] = old_input_hotkey
            self.config["stop_typing_hotkey"] = old_stop_hotkey
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

    def apply_settings_stop_typing_hotkey(self, hotkey):
        if not hotkey:
            self.ui.show_warning("hotkey", self.t("status.hotkey_empty"))
            return
        try:
            self.main_hotkey_manager.parse_hotkey(hotkey)
        except ValueError:
            self.ui.show_warning("hotkey", self.t("status.stop_hotkey_failed"))
            return

        old_hotkey = self.config.get("stop_typing_hotkey", self.config["input_hotkey"])
        self.config["stop_typing_hotkey"] = hotkey
        message = self.refresh_main_hotkey_registration(force=True)
        if message:
            self.config["stop_typing_hotkey"] = old_hotkey
            self.refresh_main_hotkey_registration(force=True)
            self.ui.show_warning("hotkey", self.t("status.stop_hotkey_failed"))
            return

        self.save_config()
        self.ui.set_status(self.t("status.stop_hotkey_applied", hotkey=hotkey), "ready")

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
        self.config["typing_interval_ms"] = round(interval_ms, 3)
        self.config["interval_ms"] = round(interval_ms, 3)
        self.save_config()
        self.ui.sync_config_controls()
        self.ui.set_status(self.t("status.interval_saved"), "ready")

    def apply_settings_target_duration(self, duration_text):
        try:
            duration_ms = float(duration_text)
        except ValueError:
            self.ui.show_warning("target_duration", self.t("status.target_duration_invalid"))
            return
        if not 1 <= duration_ms <= 10000:
            self.ui.show_warning("target_duration", self.t("status.target_duration_invalid"))
            return
        self.config["typing_target_duration_ms"] = round(duration_ms, 3)
        self.save_config()
        self.ui.sync_config_controls()
        self.ui.set_status(self.t("status.target_duration_saved"), "ready")

    def open_github(self):
        webbrowser.open(GITHUB_URL)

    def copy_email(self):
        try:
            pyperclip.copy(EMAIL)
        except Exception as e:
            self.ui.set_status(self.t("status.email_copy_failed", error=e), "error")
            return
        self.ui.set_status(self.t("status.email_copied"), "ready")

    def copy_contact_text(self, text, item):
        try:
            pyperclip.copy(text)
        except Exception as e:
            self.ui.set_status(self.t("status.contact_copy_failed", error=e), "error")
            return
        self.ui.set_status(self.t("status.contact_copied", item=item), "ready")
