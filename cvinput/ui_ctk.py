import customtkinter as ctk

from .constants import APP_NAME, APP_VERSION


class CVInputUI(ctk.CTk):
    def __init__(self, controller, config):
        super().__init__()
        self.controller = controller
        self.config = config
        self.settings_window = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(APP_NAME)
        self.geometry("320x210+980+120")
        self.minsize(280, 92)
        self.resizable(False, False)
        self.attributes("-topmost", bool(config["always_on_top"]))
        self.attributes("-alpha", float(config["opacity"]))
        self.protocol("WM_DELETE_WINDOW", controller.close)
        self.configure(fg_color="#15181d")

        self.build_main_ui()
        if config.get("mini_mode"):
            self.set_mini_mode(True)

    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="#1b1f25", corner_radius=12, border_width=1, border_color="#2a3038")
        self.main_frame.pack(fill="both", expand=True, padx=6, pady=6)

        top = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 4))

        self.title_label = ctk.CTkLabel(top, text=APP_NAME, font=("Segoe UI", 13, "bold"), text_color="#edf1f6")
        self.title_label.pack(side="left")

        self.status_dot = ctk.CTkLabel(top, text="●", font=("Segoe UI", 13), text_color="#6fb49d", width=18)
        self.status_dot.pack(side="left", padx=(6, 0))

        self.settings_button = ctk.CTkButton(
            top,
            text="⚙",
            width=28,
            height=24,
            corner_radius=7,
            fg_color="#242a33",
            hover_color="#303844",
            command=self.open_settings,
        )
        self.settings_button.pack(side="right")

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 4))

        self.text_box = ctk.CTkTextbox(
            self.content_frame,
            height=90,
            corner_radius=8,
            border_width=1,
            border_color="#303743",
            fg_color="#12151a",
            text_color="#e0e5ec",
            font=("Segoe UI", 11),
            wrap="word",
        )
        self.text_box.pack(fill="both", expand=True)

        buttons = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        buttons.pack(fill="x", pady=(7, 0))

        self.input_button = self.compact_button(buttons, "输入", self.controller.start_typing_from_button, primary=True)
        self.input_button.pack(side="left")
        self.stop_button = self.compact_button(buttons, "停止", self.controller.stop_typing)
        self.stop_button.pack(side="left", padx=(5, 0))
        self.read_button = self.compact_button(buttons, "读取", self.controller.read_clipboard_now)
        self.read_button.pack(side="left", padx=(5, 0))

        self.listen_switch = ctk.CTkSwitch(
            buttons,
            text="监听",
            width=58,
            switch_width=32,
            switch_height=17,
            progress_color="#426d64",
            button_color="#dce4ee",
            font=("Segoe UI", 11),
            command=self.controller.toggle_clipboard_listener,
        )
        self.listen_switch.pack(side="right")
        if self.config["auto_clipboard"]:
            self.listen_switch.select()

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="启动中",
            anchor="w",
            font=("Segoe UI", 10),
            text_color="#8f98a6",
            height=18,
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 7))

    def compact_button(self, parent, text, command, primary=False):
        return ctk.CTkButton(
            parent,
            text=text,
            width=52,
            height=27,
            corner_radius=7,
            fg_color="#29433f" if primary else "#242a33",
            hover_color="#34554f" if primary else "#303844",
            text_color="#edf1f6",
            font=("Segoe UI", 11),
            command=command,
        )

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus()
            return

        win = ctk.CTkToplevel(self)
        win.title("设置")
        win.geometry("310x330")
        win.resizable(False, False)
        win.transient(self)
        win.attributes("-topmost", bool(self.config["always_on_top"]))
        win.attributes("-alpha", float(self.config["opacity"]))
        win.configure(fg_color="#15181d")
        self.settings_window = win

        frame = ctk.CTkFrame(win, fg_color="#1b1f25", corner_radius=12, border_width=1, border_color="#2a3038")
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(frame, text="设置", font=("Segoe UI", 14, "bold"), text_color="#edf1f6").pack(anchor="w", padx=14, pady=(12, 8))

        self.hotkey_entry = self.setting_entry(frame, "快捷键", str(self.config["hotkey"]))
        self.interval_entry = self.setting_entry(frame, "输入间隔", str(self.config["interval"]))

        self.topmost_switch = self.setting_switch(frame, "窗口置顶", self.config["always_on_top"], self.controller.set_always_on_top)
        self.clipboard_switch = self.setting_switch(frame, "自动监听剪贴板", self.config["auto_clipboard"], self.controller.set_clipboard_listener)
        self.clear_switch = self.setting_switch(frame, "输入后清空", self.config["clear_after_input"], self.controller.set_clear_after_input)
        self.mini_switch = self.setting_switch(frame, "迷你模式", self.config["mini_mode"], self.controller.set_mini_mode)

        opacity_row = ctk.CTkFrame(frame, fg_color="transparent")
        opacity_row.pack(fill="x", padx=14, pady=(7, 2))
        ctk.CTkLabel(opacity_row, text="透明度", width=72, anchor="w", font=("Segoe UI", 11), text_color="#c6ced9").pack(side="left")
        self.opacity_slider = ctk.CTkSlider(
            opacity_row,
            from_=0.55,
            to=1.0,
            number_of_steps=45,
            progress_color="#426d64",
            button_color="#6fb49d",
            command=self.controller.set_opacity,
        )
        self.opacity_slider.set(float(self.config["opacity"]))
        self.opacity_slider.pack(side="left", fill="x", expand=True)

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(12, 8))
        ctk.CTkButton(
            actions,
            text="应用快捷键",
            height=28,
            corner_radius=7,
            fg_color="#29433f",
            hover_color="#34554f",
            command=self.apply_hotkey_from_settings,
        ).pack(side="left")
        ctk.CTkLabel(actions, text=f"v{APP_VERSION}", font=("Segoe UI", 10), text_color="#7f8998").pack(side="right")

    def setting_entry(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row, text=label, width=72, anchor="w", font=("Segoe UI", 11), text_color="#c6ced9").pack(side="left")
        entry = ctk.CTkEntry(
            row,
            height=28,
            corner_radius=7,
            border_color="#303743",
            fg_color="#12151a",
            text_color="#e0e5ec",
            font=("Segoe UI", 11),
        )
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def setting_switch(self, parent, text, value, command):
        switch = ctk.CTkSwitch(
            parent,
            text=text,
            switch_width=32,
            switch_height=17,
            progress_color="#426d64",
            button_color="#dce4ee",
            font=("Segoe UI", 11),
            command=command,
        )
        switch.pack(anchor="w", padx=14, pady=4)
        if value:
            switch.select()
        return switch

    def apply_hotkey_from_settings(self):
        hotkey = self.hotkey_entry.get().strip()
        interval_text = self.interval_entry.get().strip()
        self.controller.apply_settings_hotkey(hotkey, interval_text, self.settings_window)

    def get_text(self):
        return self.text_box.get("1.0", "end-1c")

    def set_text(self, text):
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)

    def clear_text(self):
        self.text_box.delete("1.0", "end")

    def is_text_focused(self):
        return self.focus_get() is self.text_box

    def set_status(self, text, state="ready"):
        colors = {
            "ready": "#6fb49d",
            "working": "#c7a86a",
            "error": "#d47d7d",
            "idle": "#7f8998",
        }
        self.status_dot.configure(text_color=colors.get(state, colors["ready"]))
        self.status_label.configure(text=text)

    def set_clipboard_switch(self, enabled):
        if enabled:
            self.listen_switch.select()
        else:
            self.listen_switch.deselect()

    def set_opacity_value(self, value):
        self.attributes("-alpha", float(value))
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.attributes("-alpha", float(value))

    def set_topmost_value(self, enabled):
        self.attributes("-topmost", bool(enabled))
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.attributes("-topmost", bool(enabled))

    def set_mini_mode(self, enabled):
        if enabled:
            self.content_frame.pack_forget()
            self.geometry("280x76")
        else:
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 4), before=self.status_label)
            self.geometry("320x210")

    def show_warning(self, title, message):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("280x132")
        win.resizable(False, False)
        win.transient(self)
        win.attributes("-topmost", bool(self.config["always_on_top"]))
        win.configure(fg_color="#15181d")

        frame = ctk.CTkFrame(win, fg_color="#1b1f25", corner_radius=12, border_width=1, border_color="#2a3038")
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 13, "bold"), text_color="#edf1f6").pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(frame, text=message, font=("Segoe UI", 11), text_color="#c6ced9", wraplength=230, justify="left").pack(anchor="w", padx=14)
        ctk.CTkButton(
            frame,
            text="确定",
            width=64,
            height=28,
            corner_radius=7,
            fg_color="#29433f",
            hover_color="#34554f",
            command=win.destroy,
        ).pack(anchor="e", padx=14, pady=(12, 10))
