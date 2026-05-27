SLOT_HOTKEYS = ["Alt+1", "Alt+2", "Alt+3", "Alt+4", "Alt+5", "Alt+6", "Alt+7", "Alt+8", "Alt+9", "Alt+0"]


class HotkeyController:
    def register_hotkey(self):
        toggle_message = self.refresh_toggle_hotkey_registration(force=True)
        message = self.refresh_main_hotkey_registration(force=True)
        self.refresh_slot_hotkey_registration(force=True)
        return message or toggle_message

    def refresh_toggle_hotkey_registration(self, force=False):
        hotkey = str(self.config["hotkey_toggle_hotkey"])
        if not force and self.toggle_hotkey_registered and self.registered_toggle_hotkey == hotkey:
            return None
        self.toggle_hotkey_manager.stop()
        registered, failures = self.toggle_hotkey_manager.start_all({"toggle_hotkeys": hotkey}, self.on_hotkey)
        if "toggle_hotkeys" not in registered:
            self.toggle_hotkey_registered = False
            self.registered_toggle_hotkey = None
            self.ui.set_status(self.t("status.hotkey_toggle_failed"), "error")
            return failures.get("toggle_hotkeys", self.t("status.hotkey_toggle_failed"))
        self.toggle_hotkey_registered = True
        self.registered_toggle_hotkey = hotkey
        return None

    def refresh_main_hotkey_registration(self, force=False, show_status=True):
        hotkey = str(self.config["input_hotkey"])
        if not self.config.get("hotkeys_enabled", True):
            if self.main_hotkey_registered or force:
                self.main_hotkey_manager.stop()
            self.main_hotkey_registered = False
            self.registered_main_hotkey = None
            if show_status:
                self.ui.set_status(self.t("status.hotkeys_disabled"), "idle")
            return None
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
                self.ui.set_status(self.t("status.input_hotkey_failed"), "error")
            return failures.get("main", self.t("status.input_hotkey_failed"))

        self.main_hotkey_registered = True
        self.registered_main_hotkey = hotkey
        if show_status:
            self.ui.set_status(self.t("status.hotkey_registered", hotkey=hotkey), "ready")
        return None

    def refresh_slot_hotkey_registration(self, force=False):
        if not self.config.get("hotkeys_enabled", True) or not self.config["multi_slot_enabled"]:
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
        self.schedule_ui(lambda hotkey_action=action, keys=release_keys: self.handle_hotkey(hotkey_action, keys))

    def handle_hotkey(self, action, release_keys):
        if action == "main":
            self.start_typing_from_hotkey(release_keys)
            return
        if action == "toggle_hotkeys":
            self.toggle_hotkeys_enabled_from_hotkey(release_keys)
            return
        if action.startswith("slot_"):
            self.start_typing_from_slot(int(action.split("_", 1)[1]), release_keys)

    def set_hotkeys_enabled(self, enabled):
        self.config["hotkeys_enabled"] = bool(enabled)
        self.ui.set_hotkeys_switch(bool(enabled))
        self.save_config()
        if not enabled:
            self.main_hotkey_manager.stop()
            self.slot_hotkey_manager.stop()
            self.main_hotkey_registered = False
            self.registered_main_hotkey = None
            self.slot_hotkeys_active = False
            self.ui.set_status(self.t("status.hotkeys_disabled"), "idle")
            return
        message = self.refresh_main_hotkey_registration(force=True, show_status=False)
        self.refresh_slot_hotkey_registration(force=True)
        if message:
            self.ui.set_status(self.t("status.input_hotkey_failed"), "error")
            return
        self.ui.set_status(self.t("status.hotkeys_enabled"), "ready")

    def slot_label(self, action):
        if not action.startswith("slot_"):
            return action
        index = int(action.split("_", 1)[1])
        return SLOT_HOTKEYS[index] if 0 <= index < len(SLOT_HOTKEYS) else action
