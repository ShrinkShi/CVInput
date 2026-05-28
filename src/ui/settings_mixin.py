from tkinter import filedialog
from datetime import datetime

import customtkinter as ctk

from ..constants import (
    DEFAULT_INPUT_ENCODING,
    DEFAULT_OUTPUT_ENCODING,
    DEFAULT_SINGLE_LINE_REPLACEMENT,
    DEFAULT_TYPING_MODE,
    DEFAULT_NEWLINE_SHIFT_ENTER_METHOD,
    ENCODING_AUTO,
    ENCODING_BIG5,
    ENCODING_GBK,
    ENCODING_UTF_8,
    ENCODING_UTF_8_SIG,
    NEWLINE_METHOD_KEYBOARD,
    NEWLINE_METHOD_PYNPUT,
    NEWLINE_METHOD_PYAUTOGUI,
    NEWLINE_METHOD_WIN32_SCAN,
    NEWLINE_METHOD_WIN32_VK,
    SINGLE_LINE_REPLACEMENT_SPACE,
    SINGLE_LINE_REPLACEMENT_TAB,
    TYPING_MODE_DEFAULT,
    TYPING_MODE_SINGLE_LINE,
    TYPING_MODE_SPLIT,
)
from ..debug_logger import debug_log
from .theme import ACCENT, HOVER, MUTED, SURFACE, SURFACE_DARK, TEXT


class SettingsMixin:
    def open_settings(self):
        if self.widget_exists(self.settings_window):
            self.close_settings()
            return

        self.close_about()
        self.prune_tooltips()
        debug_log(
            "WINDOW_POSITION",
            "open_settings",
            popup_type="settings",
            target_width=self.SETTINGS_SIZE[0],
            target_height=self.SETTINGS_SIZE[1],
        )
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
        self.typing_mode_row = ctk.CTkFrame(content, fg_color="transparent")
        self.typing_mode_row.pack(fill="x", pady=(2, 5))
        ctk.CTkLabel(
            self.typing_mode_row,
            text=self.t("label.typing_mode"),
            width=96,
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#c6ced9",
        ).pack(side="left")
        self.typing_mode_labels = {
            self.t("label.typing_mode.default"): TYPING_MODE_DEFAULT,
            self.t("label.typing_mode.single_line"): TYPING_MODE_SINGLE_LINE,
            self.t("label.typing_mode.split"): TYPING_MODE_SPLIT,
        }
        self.typing_mode_menu = ctk.CTkOptionMenu(
            self.typing_mode_row,
            values=list(self.typing_mode_labels.keys()),
            height=26,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            font=("Segoe UI", 10),
            command=self.on_typing_mode_selected,
        )
        self.typing_mode_menu.pack(side="left", fill="x", expand=True)
        self.apply_typing_mode_button = self.icon_button(
            self.typing_mode_row,
            "✓",
            self.apply_input_mode_from_settings,
            "tooltip.apply_mode",
        )
        self.apply_typing_mode_button.pack(side="left", padx=(5, 0))
        self.set_typing_mode_value(self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE)))
        self.add_tooltip(self.typing_mode_menu, "tooltip.setting.typing_mode")

        self.single_line_replacement_row = ctk.CTkFrame(content, fg_color="transparent")
        ctk.CTkLabel(
            self.single_line_replacement_row,
            text=self.t("label.single_line_replacement"),
            width=96,
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#c6ced9",
        ).pack(side="left")
        self.single_line_replacement_labels = {
            self.t("label.single_line_replacement.space"): SINGLE_LINE_REPLACEMENT_SPACE,
            self.t("label.single_line_replacement.tab"): SINGLE_LINE_REPLACEMENT_TAB,
        }
        self.single_line_replacement_menu = ctk.CTkOptionMenu(
            self.single_line_replacement_row,
            values=list(self.single_line_replacement_labels.keys()),
            height=26,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            font=("Segoe UI", 10),
            command=self.on_single_line_replacement_selected,
        )
        self.single_line_replacement_menu.pack(side="left", fill="x", expand=True)
        self.apply_single_line_replacement_button = self.icon_button(
            self.single_line_replacement_row,
            "✓",
            self.apply_input_mode_from_settings,
            "tooltip.apply_mode",
        )
        self.apply_single_line_replacement_button.pack(side="left", padx=(5, 0))
        self.set_single_line_replacement_value(self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT))
        self.add_tooltip(self.single_line_replacement_menu, "tooltip.setting.single_line_replacement")
        self.set_single_line_replacement_visible(self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE)))

        input_encoding_row = ctk.CTkFrame(content, fg_color="transparent")
        input_encoding_row.pack(fill="x", pady=(2, 5))
        ctk.CTkLabel(
            input_encoding_row,
            text=self.t("label.input_encoding"),
            width=96,
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#c6ced9",
        ).pack(side="left")
        self.input_encoding_labels = {
            self.t("label.encoding.auto"): ENCODING_AUTO,
            self.t("label.encoding.utf_8"): ENCODING_UTF_8,
            self.t("label.encoding.utf_8_sig"): ENCODING_UTF_8_SIG,
            self.t("label.encoding.gbk"): ENCODING_GBK,
            self.t("label.encoding.big5"): ENCODING_BIG5,
        }
        self.input_encoding_menu = ctk.CTkOptionMenu(
            input_encoding_row,
            values=list(self.input_encoding_labels.keys()),
            height=26,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            font=("Segoe UI", 10),
        )
        self.input_encoding_menu.pack(side="left", fill="x", expand=True)
        self.apply_input_encoding_button = self.icon_button(
            input_encoding_row,
            "✓",
            self.apply_encoding_from_settings,
            "tooltip.apply_encoding",
        )
        self.apply_input_encoding_button.pack(side="left", padx=(5, 0))
        self.add_tooltip(self.input_encoding_menu, "tooltip.setting.input_encoding")

        output_encoding_row = ctk.CTkFrame(content, fg_color="transparent")
        output_encoding_row.pack(fill="x", pady=(2, 5))
        ctk.CTkLabel(
            output_encoding_row,
            text=self.t("label.output_encoding"),
            width=96,
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#c6ced9",
        ).pack(side="left")
        self.output_encoding_labels = {
            self.t("label.encoding.utf_8"): ENCODING_UTF_8,
            self.t("label.encoding.utf_8_sig"): ENCODING_UTF_8_SIG,
            self.t("label.encoding.gbk"): ENCODING_GBK,
            self.t("label.encoding.big5"): ENCODING_BIG5,
        }
        self.output_encoding_menu = ctk.CTkOptionMenu(
            output_encoding_row,
            values=list(self.output_encoding_labels.keys()),
            height=26,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            font=("Segoe UI", 10),
        )
        self.output_encoding_menu.pack(side="left", fill="x", expand=True)
        self.apply_encoding_button = self.icon_button(
            output_encoding_row,
            "✓",
            self.apply_encoding_from_settings,
            "tooltip.apply_encoding",
        )
        self.apply_encoding_button.pack(side="left", padx=(5, 0))
        self.add_tooltip(self.output_encoding_menu, "tooltip.setting.output_encoding")
        self.set_encoding_values(
            self.config.get("input_encoding", DEFAULT_INPUT_ENCODING),
            self.config.get("output_encoding", DEFAULT_OUTPUT_ENCODING),
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
        self.developer_switch = self.setting_switch(
            content,
            "label.developer_mode",
            self.config.get("developer_mode", False),
            lambda: self.controller.set_developer_mode(bool(self.developer_switch.get())),
            "tooltip.setting.developer_mode",
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
        self.after(40, self.refresh_developer_debug_visibility)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def close_settings(self):
        self.close_developer_debug()
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

    def apply_input_mode_from_settings(self):
        self.controller.apply_input_mode_settings(
            self.selected_typing_mode(),
            self.selected_single_line_replacement(),
        )

    def apply_encoding_from_settings(self):
        self.controller.set_text_encodings(
            self.selected_input_encoding(),
            self.selected_output_encoding(),
        )

    def export_debug_log_from_settings(self):
        initialfile = f"CVInput-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        parent = self.settings_window if self.widget_exists(self.settings_window) else self
        path = filedialog.asksaveasfilename(
            parent=parent,
            title=self.t("label.export_debug_log"),
            defaultextension=".txt",
            initialfile=initialfile,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.controller.export_debug_log(path)

    def open_developer_debug(self):
        if not self.widget_exists(self.settings_window):
            return
        if self.widget_exists(getattr(self, "developer_debug_window", None)):
            self.place_developer_debug_window()
            self.focus_window_safely(self.developer_debug_window)
            return

        win = ctk.CTkToplevel(self)
        self.developer_debug_window = win
        self.prepare_popup(win, *self.DEVELOPER_DEBUG_SIZE)
        frame = self.popup_frame(win)
        self.popup_header(frame, "label.developer_debug", self.close_developer_debug)

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=(2, 8))

        self.debug_window_position_switch = self.setting_switch(
            content,
            "label.debug_window_position",
            self.config.get("debug_window_position", False),
            lambda: self.controller.set_debug_window_position(bool(self.debug_window_position_switch.get())),
            "tooltip.setting.debug_window_position",
        )
        self.debug_newline_behavior_switch = self.setting_switch(
            content,
            "label.debug_newline_behavior",
            self.config.get("debug_newline_behavior", False),
            lambda: self.controller.set_debug_newline_behavior(bool(self.debug_newline_behavior_switch.get())),
            "tooltip.setting.debug_newline_behavior",
        )
        backend_row = ctk.CTkFrame(content, fg_color="transparent")
        backend_row.pack(fill="x", pady=(6, 3))
        ctk.CTkLabel(
            backend_row,
            text=self.t("label.newline_backend"),
            width=88,
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#c6ced9",
        ).pack(side="left")
        self.newline_method_labels = {
            self.t("label.newline_method.pynput"): NEWLINE_METHOD_PYNPUT,
            self.t("label.newline_method.win32_scan"): NEWLINE_METHOD_WIN32_SCAN,
            self.t("label.newline_method.win32_vk"): NEWLINE_METHOD_WIN32_VK,
            self.t("label.newline_method.pyautogui"): NEWLINE_METHOD_PYAUTOGUI,
            self.t("label.newline_method.keyboard"): NEWLINE_METHOD_KEYBOARD,
        }
        self.newline_method_menu = ctk.CTkOptionMenu(
            backend_row,
            values=list(self.newline_method_labels.keys()),
            height=26,
            fg_color=SURFACE_DARK,
            button_color=ACCENT,
            button_hover_color="#34554f",
            dropdown_fg_color=SURFACE,
            font=("Segoe UI", 10),
            command=self.on_newline_method_selected,
        )
        self.newline_method_menu.pack(side="left", fill="x", expand=True)
        self.set_newline_method_value(self.config.get("newline_shift_enter_method", DEFAULT_NEWLINE_SHIFT_ENTER_METHOD))
        self.add_tooltip(self.newline_method_menu, "tooltip.setting.newline_backend")

        button_row = ctk.CTkFrame(content, fg_color="transparent")
        button_row.pack(fill="x", pady=(9, 5))
        export_button = ctk.CTkButton(
            button_row,
            text=self.t("label.export_debug_log"),
            height=26,
            corner_radius=7,
            fg_color="#242a33",
            hover_color=HOVER,
            text_color=TEXT,
            font=("Segoe UI", 10),
            command=self.export_debug_log_from_settings,
        )
        export_button.pack(side="left")
        self.add_tooltip(export_button, "tooltip.export_debug_log")

        clear_button = ctk.CTkButton(
            button_row,
            text=self.t("label.clear_debug_log"),
            height=26,
            corner_radius=7,
            fg_color="#242a33",
            hover_color=HOVER,
            text_color=TEXT,
            font=("Segoe UI", 10),
            command=self.controller.clear_debug_log_from_settings,
        )
        clear_button.pack(side="left", padx=(8, 0))
        self.add_tooltip(clear_button, "tooltip.clear_debug_log")

        self.developer_log_count_label = ctk.CTkLabel(
            content,
            text="",
            anchor="w",
            font=("Segoe UI", 10),
            text_color=MUTED,
        )
        self.developer_log_count_label.pack(fill="x", pady=(4, 0))
        self.update_developer_log_count()

        self.place_developer_debug_window()
        self.register_child_popup(win, self.close_developer_debug)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def close_developer_debug(self):
        win = getattr(self, "developer_debug_window", None)
        self.developer_debug_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except Exception:
            pass

    def refresh_developer_debug_visibility(self):
        if self.config.get("developer_mode", False) and self.widget_exists(self.settings_window):
            self.open_developer_debug()
        else:
            self.close_developer_debug()

    def update_developer_log_count(self):
        if self.widget_exists(getattr(self, "developer_log_count_label", None)):
            count = self.controller.debug_log_count()
            self.developer_log_count_label.configure(text=self.t("label.debug_log_count", count=count))

    def on_language_selected(self, label):
        language = self.language_codes.get(label, "zh_cn")
        self.controller.set_language(language)

    def on_newline_method_selected(self, label):
        method = self.newline_method_labels.get(label, DEFAULT_NEWLINE_SHIFT_ENTER_METHOD)
        self.controller.set_newline_shift_enter_method(method)

    def on_typing_mode_selected(self, label):
        mode = self.typing_mode_labels.get(label, DEFAULT_TYPING_MODE)
        self.set_single_line_replacement_visible(mode)

    def on_single_line_replacement_selected(self, label):
        return

    def selected_typing_mode(self):
        if not self.widget_exists(getattr(self, "typing_mode_menu", None)):
            return self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE))
        return self.typing_mode_labels.get(self.typing_mode_menu.get(), DEFAULT_TYPING_MODE)

    def selected_single_line_replacement(self):
        if not self.widget_exists(getattr(self, "single_line_replacement_menu", None)):
            return self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT)
        return self.single_line_replacement_labels.get(self.single_line_replacement_menu.get(), DEFAULT_SINGLE_LINE_REPLACEMENT)

    def selected_input_encoding(self):
        if not self.widget_exists(getattr(self, "input_encoding_menu", None)):
            return self.config.get("input_encoding", DEFAULT_INPUT_ENCODING)
        return self.input_encoding_labels.get(self.input_encoding_menu.get(), DEFAULT_INPUT_ENCODING)

    def selected_output_encoding(self):
        if not self.widget_exists(getattr(self, "output_encoding_menu", None)):
            return self.config.get("output_encoding", DEFAULT_OUTPUT_ENCODING)
        return self.output_encoding_labels.get(self.output_encoding_menu.get(), DEFAULT_OUTPUT_ENCODING)

    def set_disable_empty_switch(self, enabled):
        if self.widget_exists(getattr(self, "disable_empty_switch", None)):
            self.disable_empty_switch.select() if enabled else self.disable_empty_switch.deselect()

    def set_ime_switch(self, enabled):
        if self.widget_exists(getattr(self, "ime_switch", None)):
            self.ime_switch.select() if enabled else self.ime_switch.deselect()

    def set_newline_switch(self, enabled):
        if self.widget_exists(getattr(self, "newline_switch", None)):
            self.newline_switch.select() if enabled else self.newline_switch.deselect()

    def set_newline_method_value(self, method):
        if not self.widget_exists(getattr(self, "newline_method_menu", None)):
            return
        labels = getattr(self, "newline_method_labels", {})
        label = next((text for text, value in labels.items() if value == method), None)
        default_label = next(
            (text for text, value in labels.items() if value == DEFAULT_NEWLINE_SHIFT_ENTER_METHOD),
            self.t("label.newline_method.pyautogui"),
        )
        self.newline_method_menu.set(label or default_label)

    def set_typing_mode_value(self, mode):
        if not self.widget_exists(getattr(self, "typing_mode_menu", None)):
            return
        labels = getattr(self, "typing_mode_labels", {})
        label = next((text for text, value in labels.items() if value == mode), None)
        self.typing_mode_menu.set(label or self.t("label.typing_mode.default"))

    def set_single_line_replacement_value(self, replacement):
        if not self.widget_exists(getattr(self, "single_line_replacement_menu", None)):
            return
        labels = getattr(self, "single_line_replacement_labels", {})
        label = next((text for text, value in labels.items() if value == replacement), None)
        self.single_line_replacement_menu.set(label or self.t("label.single_line_replacement.space"))

    def set_encoding_values(self, input_encoding, output_encoding):
        if self.widget_exists(getattr(self, "input_encoding_menu", None)):
            input_label = next(
                (text for text, value in self.input_encoding_labels.items() if value == input_encoding),
                self.t("label.encoding.auto"),
            )
            self.input_encoding_menu.set(input_label)
        if self.widget_exists(getattr(self, "output_encoding_menu", None)):
            output_label = next(
                (text for text, value in self.output_encoding_labels.items() if value == output_encoding),
                self.t("label.encoding.utf_8"),
            )
            self.output_encoding_menu.set(output_label)

    def set_single_line_replacement_visible(self, mode):
        row = getattr(self, "single_line_replacement_row", None)
        if not self.widget_exists(row):
            return
        row.pack_forget()
        if mode == TYPING_MODE_SINGLE_LINE:
            row.pack(fill="x", pady=(2, 5), after=self.typing_mode_row)

    def set_custom_interval_switch(self, enabled):
        if self.widget_exists(getattr(self, "custom_interval_switch", None)):
            self.custom_interval_switch.select() if enabled else self.custom_interval_switch.deselect()

    def set_remember_settings_switch(self, enabled):
        if self.widget_exists(getattr(self, "remember_settings_switch", None)):
            self.remember_settings_switch.select() if enabled else self.remember_settings_switch.deselect()

    def set_close_popup_on_blur_switch(self, enabled):
        if self.widget_exists(getattr(self, "close_popup_on_blur_switch", None)):
            self.close_popup_on_blur_switch.select() if enabled else self.close_popup_on_blur_switch.deselect()

    def set_developer_switch(self, enabled):
        if self.widget_exists(getattr(self, "developer_switch", None)):
            self.developer_switch.select() if enabled else self.developer_switch.deselect()

    def set_debug_window_position_switch(self, enabled):
        if self.widget_exists(getattr(self, "debug_window_position_switch", None)):
            self.debug_window_position_switch.select() if enabled else self.debug_window_position_switch.deselect()

    def set_debug_newline_behavior_switch(self, enabled):
        if self.widget_exists(getattr(self, "debug_newline_behavior_switch", None)):
            self.debug_newline_behavior_switch.select() if enabled else self.debug_newline_behavior_switch.deselect()

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
        mode = self.config.get("input_mode", self.config.get("typing_mode", DEFAULT_TYPING_MODE))
        self.set_typing_mode_value(mode)
        self.set_single_line_replacement_value(self.config.get("single_line_replacement", DEFAULT_SINGLE_LINE_REPLACEMENT))
        self.set_single_line_replacement_visible(mode)
        self.set_encoding_values(
            self.config.get("input_encoding", DEFAULT_INPUT_ENCODING),
            self.config.get("output_encoding", DEFAULT_OUTPUT_ENCODING),
        )
        self.set_newline_method_value(self.config.get("newline_shift_enter_method", DEFAULT_NEWLINE_SHIFT_ENTER_METHOD))
        self.set_custom_interval_switch(bool(self.config["custom_interval_enabled"]))
        self.set_interval_controls_visible(bool(self.config["custom_interval_enabled"]))
        self.set_multi_slot_visible(bool(self.config["multi_slot_enabled"]))
        self.set_close_to_tray_switch(bool(self.config["close_to_tray"]))
        self.set_startup_switch(bool(self.config["startup_on_boot"]))
        self.set_remember_settings_switch(bool(self.config["remember_settings"]))
        self.set_close_popup_on_blur_switch(bool(self.config["close_popup_on_blur"]))
        self.set_developer_switch(bool(self.config.get("developer_mode", False)))
        self.set_debug_window_position_switch(bool(self.config.get("debug_window_position", False)))
        self.set_debug_newline_behavior_switch(bool(self.config.get("debug_newline_behavior", False)))
        self.refresh_developer_debug_visibility()
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
