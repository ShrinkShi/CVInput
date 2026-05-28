import pyperclip

from ..constants import (
    DEFAULT_TYPING_MODE,
    ENCODING_AUTO,
    ENCODING_BIG5,
    ENCODING_GBK,
    ENCODING_UTF_8,
    ENCODING_UTF_8_SIG,
    SINGLE_LINE_REPLACEMENT_TAB,
    TYPING_MODE_SINGLE_LINE,
    TYPING_MODE_SPLIT,
)
from ..debug_logger import debug_log


class ClipboardController:
    def schedule_clipboard_update(self, text):
        self.schedule_ui(lambda value=text: self.update_text_from_clipboard(value))

    def update_text_from_clipboard(self, text, force=False):
        if self.ui.is_text_focused() and not force:
            return
        text = self.normalize_clipboard_text(text)
        self.ui.set_raw_text(text)
        self.apply_mode_to_raw_text(text)

    def apply_mode_to_raw_text(self, text=None):
        if text is None:
            text = self.ui.get_raw_text()
        text = self.normalize_clipboard_text(text)
        mode = self.current_input_mode()
        if mode == TYPING_MODE_SPLIT:
            self.create_split_queue(text)
            return
        if mode == TYPING_MODE_SINGLE_LINE:
            self.clear_split_queue()
            self.ui.set_text(self.single_line_clipboard_text(text))
            self.refresh_main_hotkey_registration()
            return
        self.clear_split_queue()
        self.ui.set_text(text)
        self.refresh_main_hotkey_registration()

    def on_raw_text_changed(self):
        self.apply_mode_to_raw_text(self.ui.get_raw_text())

    def normalize_clipboard_text(self, text):
        return self.decode_input_text(text).replace("\r\n", "\n").replace("\r", "\n")

    def current_input_mode(self):
        return self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE))

    def decode_input_text(self, text):
        if isinstance(text, str):
            return text
        if text is None:
            return ""
        if not isinstance(text, (bytes, bytearray)):
            return str(text)
        raw = bytes(text)
        encoding = self.config.get("input_encoding", ENCODING_AUTO)
        candidates = [encoding] if encoding != ENCODING_AUTO else [
            ENCODING_UTF_8_SIG,
            ENCODING_UTF_8,
            ENCODING_GBK,
            ENCODING_BIG5,
        ]
        for candidate in candidates:
            try:
                return raw.decode(candidate)
            except UnicodeDecodeError:
                continue
        return raw.decode(ENCODING_UTF_8, errors="replace")

    def single_line_clipboard_text(self, text):
        replacement = "\t" if self.config.get("single_line_replacement") == SINGLE_LINE_REPLACEMENT_TAB else " "
        return self.normalize_clipboard_text(text).replace("\n", replacement)

    def on_main_text_changed(self):
        self.refresh_main_hotkey_registration()

    def read_clipboard_now(self):
        try:
            text = pyperclip.paste()
        except Exception as e:
            self.ui.set_status(self.t("status.clipboard_failed", error=e), "error")
            return
        self.update_text_from_clipboard(text, force=True)

    def create_split_queue(self, text):
        self.split_lines = [line for line in self.normalize_clipboard_text(text).splitlines() if line.strip()]
        self.split_index = 0
        debug_log("NEWLINE_BEHAVIOR", "split_created", line_count=len(self.split_lines))
        if not self.split_lines:
            self.ui.clear_text()
            self.refresh_main_hotkey_registration(force=True)
            return
        self.show_split_current_line()

    def clear_split_queue(self):
        self.split_lines = []
        self.split_index = 0

    def show_split_current_line(self):
        total = len(self.split_lines)
        if not total or self.split_index >= total:
            return
        self.ui.set_text(self.split_lines[self.split_index])
        current = self.split_index + 1
        self.ui.set_status(self.t("status.split_position", current=current, total=total), "ready")
        debug_log("NEWLINE_BEHAVIOR", "split_current_line", index=current, total=total)
        self.refresh_main_hotkey_registration(force=True)

    def advance_split_queue(self):
        total = len(self.split_lines)
        if not total:
            return False
        self.split_index += 1
        if self.split_index < total:
            current = self.split_index + 1
            debug_log("NEWLINE_BEHAVIOR", "split_advance", index=current, total=total)
            self.show_split_current_line()
            return True
        debug_log("NEWLINE_BEHAVIOR", "split_finished", total=total)
        self.clear_split_queue()
        self.ui.clear_text()
        self.refresh_main_hotkey_registration(force=True)
        self.ui.set_status(self.t("status.split_finished"), "ready")
        return True

    def set_clipboard_listener(self, enabled):
        self.config["auto_clipboard"] = bool(enabled)
        self.clipboard_monitor.set_enabled(bool(enabled))
        self.ui.set_clipboard_switch(bool(enabled))
        self.save_config()
        self.ui.set_status(
            self.t("status.clipboard_on") if enabled else self.t("status.clipboard_off"),
            "ready" if enabled else "idle",
        )
