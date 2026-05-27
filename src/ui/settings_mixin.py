import customtkinter as ctk

from .theme import ACCENT, HOVER, MUTED, SURFACE, SURFACE_DARK, TEXT


class SettingsMixin:
    def open_settings(self):
        if self.widget_exists(self.settings_window):
            self.place_child_window_near_main(self.settings_window, *self.SETTINGS_SIZE)
            self.focus_window_safely(self.settings_window)
            return

        self.close_about()
        self.prune_tooltips()
        win = ctk.CTkToplevel(self)
        self.settings_window = win
        self.prepare_popup(win, *self.SETTINGS_SIZE)
        frame = self.popup_frame(win)
        self.popup_header(frame, "label.settings", self.close_settings)

        content = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=0, height=295)
        content.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        hotkey_row = ctk.CTkFrame(content, fg_color="transparent")
        hotkey_row.pack(fill="x", pady=(2, 5))
        ctk.CTkLabel(hotkey_row, text=self.t("label.input_hotkey"), width=96, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        self.input_hotkey_entry = self.setting_entry(hotkey_row, str(self.config["input_hotkey"]))
        self.input_hotkey_entry.pack(side="left", fill="x", expand=True)
        self.hotkey_entry = self.input_hotkey_entry
        self.apply_hotkey_button = self.icon_button(hotkey_row, "✓", self.apply_input_hotkey_from_settings, "tooltip.apply_hotkey")
        self.apply_hotkey_button.pack(side="left", padx=(5, 0))

        hotkey_toggle_row = ctk.CTkFrame(content, fg_color="transparent")
        hotkey_toggle_row.pack(fill="x", pady=(2, 5))
        ctk.CTkLabel(hotkey_toggle_row, text=self.t("label.hotkey_toggle_hotkey"), width=96, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        self.hotkey_toggle_entry = self.setting_entry(hotkey_toggle_row, str(self.config["hotkey_toggle_hotkey"]))
        self.hotkey_toggle_entry.pack(side="left", fill="x", expand=True)
        self.apply_hotkey_toggle_button = self.icon_button(
            hotkey_toggle_row,
            "✓",
            self.apply_hotkey_toggle_from_settings,
            "tooltip.apply_hotkey",
        )
        self.apply_hotkey_toggle_button.pack(side="left", padx=(5, 0))

        interval_row = ctk.CTkFrame(content, fg_color="transparent")
        interval_row.pack(fill="x", pady=4)
        ctk.CTkLabel(interval_row, text=self.t("label.interval"), width=88, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        self.custom_interval_switch = self.setting_switch(
            content,
            "label.custom_interval_enabled",
            self.config["custom_interval_enabled"],
            lambda: self.controller.set_custom_interval_enabled(bool(self.custom_interval_switch.get())),
            "tooltip.setting.custom_interval_enabled",
        )

        self.interval_row = interval_row
        self.interval_entry = self.setting_entry(interval_row, str(self.config["interval_ms"]))
        self.interval_entry.pack(side="left", fill="x", expand=True)
        self.apply_interval_button = self.icon_button(interval_row, "✓", self.apply_interval_from_settings, "tooltip.apply_interval")
        self.apply_interval_button.pack(side="left", padx=(5, 0))
        self.set_interval_controls_visible(bool(self.config["custom_interval_enabled"]))

        self.clipboard_switch = self.setting_switch(
            content,
            "label.auto_clipboard",
            self.config["auto_clipboard"],
            lambda: self.controller.set_clipboard_listener(bool(self.clipboard_switch.get())),
            "tooltip.setting.auto_clipboard",
        )
        self.clear_switch = self.setting_switch(
            content,
            "label.clear_after_typing",
            self.config["clear_after_input"],
            lambda: self.controller.set_clear_after_input(bool(self.clear_switch.get())),
            "tooltip.setting.clear_after_typing",
        )
        self.disable_empty_switch = self.setting_switch(
            content,
            "label.disable_hotkey_when_clipboard_empty",
            self.config["disable_hotkey_when_clipboard_empty"],
            lambda: self.controller.set_disable_hotkey_when_clipboard_empty(bool(self.disable_empty_switch.get())),
            "tooltip.setting.disable_hotkey_when_clipboard_empty",
        )
        self.ime_switch = self.setting_switch(
            content,
            "label.toggle_ime_with_shift",
            self.config["toggle_ime_with_shift"],
            lambda: self.controller.set_toggle_ime_with_shift(bool(self.ime_switch.get())),
            "tooltip.setting.toggle_ime_with_shift",
        )
        self.newline_switch = self.setting_switch(
            content,
            "label.newline_with_shift_enter",
            self.config["newline_with_shift_enter"],
            lambda: self.controller.set_newline_with_shift_enter(bool(self.newline_switch.get())),
            "tooltip.setting.newline_with_shift_enter",
        )
        self.multi_slot_switch = self.setting_switch(
            content,
            "label.multi_slot_enabled",
            self.config["multi_slot_enabled"],
            lambda: self.controller.set_multi_slot_enabled(bool(self.multi_slot_switch.get())),
            "tooltip.setting.multi_slot_enabled",
        )
        self.close_to_tray_switch = self.setting_switch(
            content,
            "label.close_to_tray",
            self.config["close_to_tray"],
            lambda: self.controller.set_close_to_tray(bool(self.close_to_tray_switch.get())),
            "tooltip.setting.close_to_tray",
        )
        self.startup_switch = self.setting_switch(
            content,
            "label.startup_on_boot",
            self.config["startup_on_boot"],
            lambda: self.controller.set_startup_on_boot(bool(self.startup_switch.get())),
            "tooltip.setting.startup_on_boot",
        )
        self.remember_settings_switch = self.setting_switch(
            content,
            "label.remember_settings",
            self.config["remember_settings"],
            lambda: self.controller.set_remember_settings(bool(self.remember_settings_switch.get())),
            "tooltip.setting.remember_settings",
        )
        self.close_popup_on_blur_switch = self.setting_switch(
            content,
            "label.close_popup_on_blur",
            self.config["close_popup_on_blur"],
            lambda: self.controller.set_close_popup_on_blur(bool(self.close_popup_on_blur_switch.get())),
            "tooltip.setting.close_popup_on_blur",
        )

        opacity_row = ctk.CTkFrame(content, fg_color="transparent")
        opacity_row.pack(fill="x", pady=(7, 3))
        ctk.CTkLabel(opacity_row, text=self.t("label.opacity"), width=88, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        self.opacity_slider = ctk.CTkSlider(
            opacity_row,
            from_=0.55,
            to=1.0,
            height=12,
            number_of_steps=45,
            progress_color=ACCENT,
            button_color="#6fb49d",
            command=self.controller.set_opacity,
        )
        self.opacity_slider.set(float(self.config["opacity"]))
        self.opacity_slider.pack(side="left", fill="x", expand=True)

        language_row = ctk.CTkFrame(content, fg_color="transparent")
        language_row.pack(fill="x", pady=(7, 3))
        ctk.CTkLabel(language_row, text=self.t("label.language"), width=88, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        self.language_codes = {
            self.t("label.language.zh_cn"): "zh_cn",
            self.t("label.language.en_us"): "en_us",
        }
        self.language_menu = ctk.CTkOptionMenu(
            language_row,
            values=list(self.language_codes.keys()),
            width=150,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            command=self.on_language_selected,
        )
        current_label = self.t(f"label.language.{self.config['language']}")
        self.language_menu.set(current_label)
        self.language_menu.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            content,
            text=self.t("label.restore_defaults"),
            height=26,
            corner_radius=7,
            fg_color="#242a33",
            hover_color=HOVER,
            text_color=TEXT,
            font=("Segoe UI", 10),
            command=self.controller.restore_default_settings,
        ).pack(anchor="w", pady=(9, 4))

        self.settings_status = ctk.CTkLabel(frame, text="", anchor="w", font=("Segoe UI", 10), text_color=MUTED, height=18)
        self.settings_status.pack(fill="x", padx=14, pady=(0, 10))
        self.place_child_window_near_main(win, *self.SETTINGS_SIZE)
        self.register_child_popup(win, self.close_settings)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def close_settings(self):
        win = self.settings_window
        self.settings_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except Exception:
            pass

    def apply_hotkey_from_settings(self):
        self.apply_input_hotkey_from_settings()

    def apply_input_hotkey_from_settings(self):
        self.controller.apply_settings_input_hotkey(self.input_hotkey_entry.get().strip())

    def apply_hotkey_toggle_from_settings(self):
        self.controller.apply_settings_hotkey_toggle_hotkey(self.hotkey_toggle_entry.get().strip())

    def apply_interval_from_settings(self):
        self.controller.apply_settings_interval(self.interval_entry.get().strip())

    def on_language_selected(self, label):
        language = self.language_codes.get(label, "zh_cn")
        self.controller.set_language(language)

    def set_disable_empty_switch(self, enabled):
        if self.widget_exists(getattr(self, "disable_empty_switch", None)):
            self.disable_empty_switch.select() if enabled else self.disable_empty_switch.deselect()

    def set_ime_switch(self, enabled):
        if self.widget_exists(getattr(self, "ime_switch", None)):
            self.ime_switch.select() if enabled else self.ime_switch.deselect()

    def set_newline_switch(self, enabled):
        if self.widget_exists(getattr(self, "newline_switch", None)):
            self.newline_switch.select() if enabled else self.newline_switch.deselect()

    def set_custom_interval_switch(self, enabled):
        if self.widget_exists(getattr(self, "custom_interval_switch", None)):
            self.custom_interval_switch.select() if enabled else self.custom_interval_switch.deselect()

    def set_remember_settings_switch(self, enabled):
        if self.widget_exists(getattr(self, "remember_settings_switch", None)):
            self.remember_settings_switch.select() if enabled else self.remember_settings_switch.deselect()

    def set_close_popup_on_blur_switch(self, enabled):
        if self.widget_exists(getattr(self, "close_popup_on_blur_switch", None)):
            self.close_popup_on_blur_switch.select() if enabled else self.close_popup_on_blur_switch.deselect()

    def set_interval_controls_visible(self, enabled):
        if not self.widget_exists(getattr(self, "interval_row", None)):
            return
        self.interval_row.pack_forget()
        if enabled:
            self.interval_row.pack(fill="x", pady=4, after=self.custom_interval_switch)

    def refresh_popup_blur_behavior(self):
        if self.config.get("close_popup_on_blur", False):
            if self.child_popups and self.outside_click_binding is None:
                self.bind_outside_click_close()
            return
        if self.outside_click_binding is not None:
            self.unbind("<ButtonPress-1>", self.outside_click_binding)
            self.outside_click_binding = None

    def set_startup_switch(self, enabled):
        if self.widget_exists(getattr(self, "startup_switch", None)):
            self.startup_switch.select() if enabled else self.startup_switch.deselect()

    def set_close_to_tray_switch(self, enabled):
        if self.widget_exists(getattr(self, "close_to_tray_switch", None)):
            self.close_to_tray_switch.select() if enabled else self.close_to_tray_switch.deselect()

    def sync_config_controls(self):
        self.set_clipboard_switch(bool(self.config["auto_clipboard"]))
        self.set_disable_empty_switch(bool(self.config["disable_hotkey_when_clipboard_empty"]))
        self.set_ime_switch(bool(self.config["toggle_ime_with_shift"]))
        self.set_newline_switch(bool(self.config["newline_with_shift_enter"]))
        self.set_custom_interval_switch(bool(self.config["custom_interval_enabled"]))
        self.set_interval_controls_visible(bool(self.config["custom_interval_enabled"]))
        self.set_multi_slot_visible(bool(self.config["multi_slot_enabled"]))
        self.set_close_to_tray_switch(bool(self.config["close_to_tray"]))
        self.set_startup_switch(bool(self.config["startup_on_boot"]))
        self.set_remember_settings_switch(bool(self.config["remember_settings"]))
        self.set_close_popup_on_blur_switch(bool(self.config["close_popup_on_blur"]))
        self.set_hotkeys_switch(bool(self.config.get("hotkeys_enabled", True)))
        self.set_topmost_value(bool(self.config["always_on_top"]))
        self.set_opacity_value(float(self.config["opacity"]))
        if self.widget_exists(getattr(self, "clear_switch", None)):
            self.clear_switch.select() if self.config["clear_after_input"] else self.clear_switch.deselect()
        if self.widget_exists(getattr(self, "input_hotkey_entry", None)):
            self.replace_entry_text(self.input_hotkey_entry, str(self.config["input_hotkey"]))
        if self.widget_exists(getattr(self, "hotkey_toggle_entry", None)):
            self.replace_entry_text(self.hotkey_toggle_entry, str(self.config["hotkey_toggle_hotkey"]))
        if self.widget_exists(getattr(self, "interval_entry", None)):
            self.replace_entry_text(self.interval_entry, str(self.config["interval_ms"]))
        if self.widget_exists(getattr(self, "opacity_slider", None)):
            self.opacity_slider.set(float(self.config["opacity"]))
        if self.widget_exists(getattr(self, "language_menu", None)):
            self.language_menu.set(self.t(f"label.language.{self.config['language']}"))
        for index, entry in enumerate(getattr(self, "slot_entries", [])):
            text = self.config["multi_slots"][index] if index < len(self.config["multi_slots"]) else ""
            self.replace_textbox_text(entry, text)
