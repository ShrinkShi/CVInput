import threading

from ..constants import (
    DEFAULT_INTERVAL_MS,
    DEFAULT_NEWLINE_SHIFT_ENTER_METHOD,
    DEFAULT_SINGLE_LINE_REPLACEMENT,
    DEFAULT_TYPING_MODE,
    SINGLE_LINE_REPLACEMENT_TAB,
    TYPING_MODE_SINGLE_LINE,
    TYPING_MODE_SPLIT,
)
from ..ime import maybe_toggle_ime_before_typing, restore_ime_after_typing


class TypingController:
    def toggle_hotkeys_enabled_from_hotkey(self, release_keys):
        self.typing_engine._release_trigger_keys(release_keys)
        self.set_hotkeys_enabled(not bool(self.config.get("hotkeys_enabled", True)))

    def start_typing_from_hotkey(self, release_keys):
        if self.config["disable_hotkey_when_clipboard_empty"] and not self.ui.get_text().strip():
            self.refresh_main_hotkey_registration(force=True)
            return
        self.start_typing(release_keys, input_source="main_text_hotkey")

    def start_typing_from_slot(self, index, release_keys):
        slots = self.config.get("multi_slots", [])
        text = slots[index] if 0 <= index < len(slots) else ""
        if not text:
            self.ui.set_status(self.t("status.slot_empty", slot=self.slot_label(f"slot_{index}")), "idle")
            return
        self.start_typing(release_keys, text=text, input_source=f"slot_{index}")

    def start_typing_from_button(self):
        self.start_typing([], input_source="button")

    def start_typing(self, release_keys, text=None, input_source="unknown"):
        if self.typing_thread and self.typing_thread.is_alive():
            return
        if text is None:
            text = self.ui.get_text()
        if not text:
            self.ui.set_status(self.t("status.text_empty"), "idle")
            return

        self.print_input_mode_debug(text, input_source)
        self.typing_stop_event.clear()
        self.ui.reset_input_progress()
        self.ui.set_status(self.t("status.typing"), "working")
        self.typing_thread = threading.Thread(
            target=self._typing_worker,
            args=(text, self.input_interval_seconds(), release_keys, input_source),
            daemon=True,
        )
        self.typing_thread.start()

    def print_input_mode_debug(self, text, input_source):
        mode = self.current_input_mode()
        replacement = self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT)
        split_lines = getattr(self, "split_lines", [])
        raw_text = str(text)
        line_count = len(split_lines) if mode == TYPING_MODE_SPLIT and split_lines else len(raw_text.splitlines())
        processed_text = raw_text
        if mode in (TYPING_MODE_SINGLE_LINE, TYPING_MODE_SPLIT):
            newline_replacement = "\t" if replacement == SINGLE_LINE_REPLACEMENT_TAB else " "
            processed_text = raw_text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline_replacement)
        preview = processed_text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(
            "[INPUT_MODE] "
            f"source={input_source} "
            f"mode={mode} "
            f"single_line_replacement={replacement} "
            f"split_index={getattr(self, 'split_index', 0)} "
            f"split_queue_size={len(split_lines)} "
            f"line_count={line_count} "
            f"processed_text_preview={preview!r}"
        )

    def current_input_mode(self):
        return self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE))

    def input_interval_seconds(self):
        interval_ms = DEFAULT_INTERVAL_MS
        if self.config.get("custom_interval_enabled", False):
            try:
                interval_ms = float(self.config.get("interval_ms", DEFAULT_INTERVAL_MS))
            except (TypeError, ValueError):
                interval_ms = DEFAULT_INTERVAL_MS
        return interval_ms / 1000

    def _typing_worker(self, text, interval, release_keys, input_source):
        should_restore_ime = False
        try:
            should_restore_ime = maybe_toggle_ime_before_typing(self.config)
            progress_callback = lambda done, total: self.schedule_ui(
                lambda current=done, count=total: self.ui.set_input_progress(current, count)
            )
            self.typing_engine.type_text(
                text,
                interval,
                self.typing_stop_event,
                release_keys,
                self.config.get("newline_shift_enter_method", DEFAULT_NEWLINE_SHIFT_ENTER_METHOD),
                self.current_input_mode(),
                self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT),
                progress_callback,
                input_source,
            )
            stopped = self.typing_stop_event.is_set()
            self.schedule_ui(lambda source=input_source: self.on_typing_done(stopped, source))
        except Exception as e:
            self.schedule_ui(lambda message=str(e): self.on_typing_error(message))
        finally:
            restore_ime_after_typing(should_restore_ime)

    def on_typing_done(self, stopped, input_source="unknown"):
        if (
            not stopped
            and self.current_input_mode() == TYPING_MODE_SPLIT
            and input_source in ("main_text_hotkey", "button")
            and self.advance_split_queue()
        ):
            return
        self.ui.set_status(self.t("status.stopped") if stopped else self.t("status.done"), "ready")
        if not stopped and self.config["clear_after_input"]:
            self.ui.clear_text()
            self.ui.clear_raw_text()
            self.refresh_main_hotkey_registration()

    def on_typing_error(self, message):
        self.ui.set_status(self.t("status.typing_failed", error=message), "error")

    def stop_typing(self):
        self.typing_stop_event.set()
        self.ui.set_status(self.t("status.stopping"), "working")
