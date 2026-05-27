import pyperclip


class ClipboardController:
    def schedule_clipboard_update(self, text):
        self.schedule_ui(lambda value=text: self.update_text_from_clipboard(value))

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
