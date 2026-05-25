import sys
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .constants import APP_NAME, APP_VERSION


SURFACE = "#1b1f25"
SURFACE_DARK = "#14171c"
PANEL = "#171a20"
BORDER = "#2a3038"
HOVER = "#29303a"
ACCENT = "#426d64"
TEXT = "#e8edf4"
MUTED = "#8f98a6"
TRANSPARENT_KEY = "#010203"


def resource_path(relative_path):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative_path


def widget_exists(widget):
    try:
        return widget is not None and bool(widget.winfo_exists())
    except Exception:
        return False


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.after_id = None
        try:
            self.parent = widget._root()
        except Exception:
            self.parent = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def set_text(self, text):
        self.text = text

    def schedule(self, _event=None):
        self.hide()
        if not widget_exists(self.widget) or not widget_exists(self.parent):
            return
        try:
            self.after_id = self.parent.after(350, self.show)
        except Exception:
            self.after_id = None

    def show(self):
        self.after_id = None
        if widget_exists(self.tip) or not widget_exists(self.widget) or not widget_exists(self.parent):
            return
        try:
            owner = self.widget.winfo_toplevel()
            if not widget_exists(owner):
                return
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
            self.tip = ctk.CTkToplevel(self.parent)
            self.tip.overrideredirect(True)
            self.tip.attributes("-topmost", True)
            self.tip.configure(fg_color=TRANSPARENT_KEY)
            try:
                self.tip.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
            except tk.TclError:
                self.tip.configure(fg_color="#252b34")
            self.tip.geometry(f"+{x}+{y}")
            ctk.CTkLabel(
                self.tip,
                text=self.text,
                fg_color="#252b34",
                text_color="#dce3ec",
                corner_radius=5,
                font=("Segoe UI", 10),
            ).pack(padx=1, pady=1, ipadx=7, ipady=3)
        except Exception:
            self.hide()

    def hide(self, _event=None):
        if self.after_id is not None:
            try:
                if widget_exists(self.parent):
                    self.parent.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        tip = self.tip
        self.tip = None
        try:
            if widget_exists(tip):
                tip.destroy()
        except Exception:
            pass


class CVInputUI(ctk.CTk):
    WIDTH = 380
    HEIGHT = 210
    EXPANDED_HEIGHT = 620
    SLOT_FRAME_HEIGHT = 392
    SLOT_TEXTBOX_HEIGHT = 30
    SETTINGS_SIZE = (344, 486)
    ABOUT_SIZE = (430, 620)

    def __init__(self, controller, config):
        super().__init__()
        self.controller = controller
        self.config = config
        self.settings_window = None
        self.about_window = None
        self.tooltips = {}
        self.drag_x = 0
        self.drag_y = 0
        self.popup_drag_x = 0
        self.popup_drag_y = 0
        self.map_binding = None
        self.language_codes = {}
        self.multi_slot_frame = None
        self.slot_entries = []
        self.child_popups = []
        self.outside_click_binding = None
        self.is_multi_slot_visible = False
        self.interval_row = None
        self.settings_icon = self.load_icon("set.png")
        self.about_icon = self.load_icon("about.png")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(APP_NAME)
        self.overrideredirect(True)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+980+120")
        self.resizable(False, False)
        self.attributes("-topmost", bool(config["always_on_top"]))
        self.attributes("-alpha", float(config["opacity"]))
        self.protocol("WM_DELETE_WINDOW", controller.close)
        self.apply_transparent_background(self)

        self.build_main_ui()
        self.set_multi_slot_visible(bool(self.config["multi_slot_enabled"]))
        self.refresh_texts(rebuild_popups=False)

    def t(self, key, **kwargs):
        return self.controller.t(key, **kwargs)

    def build_main_ui(self):
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=SURFACE,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        self.main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self.titlebar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=48)
        self.titlebar.pack(fill="x", padx=8, pady=(5, 2))
        self.titlebar.pack_propagate(False)
        self.titlebar.grid_columnconfigure(0, weight=0, minsize=76)
        self.titlebar.grid_columnconfigure(1, weight=1)
        self.titlebar.grid_columnconfigure(2, weight=0, minsize=104)

        self.left_tools = ctk.CTkFrame(self.titlebar, fg_color="transparent")
        self.left_tools.grid(row=0, column=0, sticky="w")
        self.settings_button = self.icon_button(
            self.left_tools,
            "" if self.settings_icon else "⚙",
            self.open_settings,
            "tooltip.settings",
            image=self.settings_icon,
        )
        self.settings_button.pack(side="left")
        self.about_button = self.icon_button(
            self.left_tools,
            "" if self.about_icon else "ⓘ",
            self.open_about,
            "tooltip.about",
            image=self.about_icon,
        )
        self.about_button.pack(side="left", padx=(2, 0))

        self.title_group = ctk.CTkFrame(self.titlebar, fg_color="transparent")
        self.title_group.grid(row=0, column=1, sticky="nsew")
        self.title_label = ctk.CTkLabel(self.title_group, text="", font=("Segoe UI", 13, "bold"), text_color=TEXT, height=20)
        self.title_label.pack(anchor="center", pady=(2, 0))
        self.subtitle_label = ctk.CTkLabel(self.title_group, text="", font=("Segoe UI", 9), text_color=MUTED, height=16)
        self.subtitle_label.pack(anchor="center")

        self.right_tools = ctk.CTkFrame(self.titlebar, fg_color="transparent")
        self.right_tools.grid(row=0, column=2, sticky="e")
        self.pin_button = self.icon_button(self.right_tools, "📌", self.controller.toggle_always_on_top, "tooltip.pin")
        self.pin_button.pack(side="left")
        self.minimize_button = self.icon_button(self.right_tools, "-", self.minimize_window, "tooltip.minimize")
        self.minimize_button.pack(side="left", padx=(2, 0))
        self.close_button = self.icon_button(self.right_tools, "×", self.controller.close, "tooltip.close")
        self.close_button.pack(side="left", padx=(2, 0))

        for widget in (self.titlebar, self.title_group, self.title_label, self.subtitle_label):
            widget.bind("<ButtonPress-1>", self.start_drag, add="+")
            widget.bind("<B1-Motion>", self.drag_window, add="+")

        self.preview_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.preview_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.text_box = ctk.CTkTextbox(
            self.preview_frame,
            height=76,
            corner_radius=9,
            border_width=1,
            border_color="#303743",
            fg_color=SURFACE_DARK,
            text_color=TEXT,
            font=("Segoe UI", 11),
            wrap="word",
        )
        self.text_box.pack(fill="x")
        self.text_box.bind("<KeyRelease>", lambda _event: self.controller.on_main_text_changed(), add="+")
        self.text_box.bind("<FocusOut>", lambda _event: self.controller.on_main_text_changed(), add="+")

        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=29)
        self.action_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.action_frame.pack_propagate(False)
        self.input_button = self.icon_button(
            self.action_frame,
            "✍️",
            self.controller.start_typing_from_button,
            "tooltip.type",
            text_color="#6fb49d",
            font=("Segoe UI Emoji", 13),
        )
        self.input_button.pack(side="left")
        self.stop_button = self.icon_button(
            self.action_frame,
            "■",
            self.controller.stop_typing,
            "tooltip.stop",
            text_color="#d47d7d",
        )
        self.stop_button.pack(side="left", padx=(3, 0))
        self.read_button = self.icon_button(
            self.action_frame,
            "📄",
            self.controller.read_clipboard_now,
            "tooltip.read_clipboard",
            font=("Segoe UI Emoji", 13),
        )
        self.read_button.pack(side="left", padx=(3, 0))
        self.progress_bar = ctk.CTkProgressBar(
            self.action_frame,
            width=78,
            height=5,
            corner_radius=4,
            fg_color="#242a33",
            progress_color="#6fb49d",
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=(8, 0), pady=(10, 0))
        self.progress_percent_label = ctk.CTkLabel(
            self.action_frame,
            text="",
            width=38,
            anchor="w",
            font=("Segoe UI", 9),
            text_color=MUTED,
        )
        self.progress_percent_label.pack(side="left", padx=(5, 0), pady=(3, 0))

        self.hotkeys_switch = ctk.CTkSwitch(
            self.action_frame,
            text="",
            width=54,
            switch_width=30,
            switch_height=16,
            progress_color=ACCENT,
            button_color="#dce4ee",
            font=("Segoe UI", 10),
            command=lambda: self.controller.set_hotkeys_enabled(bool(self.hotkeys_switch.get())),
        )
        self.hotkeys_switch.pack(side="right", pady=(4, 0))
        if self.config.get("hotkeys_enabled", True):
            self.hotkeys_switch.select()

        self.listen_switch = ctk.CTkSwitch(
            self.action_frame,
            text="",
            width=54,
            switch_width=30,
            switch_height=16,
            progress_color=ACCENT,
            button_color="#dce4ee",
            font=("Segoe UI", 10),
            command=lambda: self.controller.set_clipboard_listener(bool(self.listen_switch.get())),
        )
        self.listen_switch.pack(side="right", padx=(0, 8), pady=(4, 0))
        if self.config["auto_clipboard"]:
            self.listen_switch.select()

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            anchor="w",
            font=("Segoe UI", 10),
            text_color=MUTED,
            height=18,
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 8))

    def load_icon(self, filename):
        path = resource_path(Path("assets") / filename)
        try:
            image = Image.open(path)
        except (FileNotFoundError, OSError):
            return None
        return ctk.CTkImage(light_image=image, dark_image=image, size=(16, 16))

    def icon_button(self, parent, text, command, tooltip_key, text_color="#c7d0dc", font=("Segoe UI Symbol", 13), image=None):
        button = ctk.CTkButton(
            parent,
            text=text,
            image=image,
            width=25,
            height=25,
            corner_radius=6,
            border_width=0,
            fg_color="transparent",
            hover_color=HOVER,
            text_color=text_color,
            font=font,
            command=command,
        )
        self.tooltips[button] = (tooltip_key, Tooltip(button, self.t(tooltip_key)))
        return button

    def prune_tooltips(self):
        for button, (_key, tooltip) in list(self.tooltips.items()):
            if not widget_exists(button):
                tooltip.hide()
                self.tooltips.pop(button, None)

    def hide_tooltips_for_window(self, win):
        for button, (_key, tooltip) in list(self.tooltips.items()):
            if not widget_exists(button) or (self.widget_exists(win) and self.widget_belongs_to_window(button, win)):
                tooltip.hide()
                self.tooltips.pop(button, None)

    def focus_window_safely(self, win):
        if not self.widget_exists(win):
            return
        try:
            win.lift()
            win.focus_force()
        except tk.TclError:
            pass

    def refresh_texts(self, rebuild_popups=True):
        self.title_label.configure(text=self.t("app.title"))
        self.subtitle_label.configure(text=self.t("app.subtitle"))
        self.listen_switch.configure(text=self.t("label.listen"))
        self.hotkeys_switch.configure(text=self.t("label.hotkeys"))
        for _button, (key, tooltip) in self.tooltips.items():
            tooltip.set_text(self.t(key))
        self.update_pin_button(bool(self.config["always_on_top"]))
        if rebuild_popups:
            settings_open = self.widget_exists(self.settings_window)
            about_open = self.widget_exists(self.about_window)
            if settings_open:
                self.close_settings()
                self.after(10, self.open_settings)
            if about_open:
                self.close_about()
                self.after(10, self.open_about)

    def open_settings(self):
        if self.widget_exists(self.settings_window):
            self.place_settings_window_near_main(self.settings_window, *self.SETTINGS_SIZE)
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
        )
        self.clear_switch = self.setting_switch(
            content,
            "label.clear_after_typing",
            self.config["clear_after_input"],
            lambda: self.controller.set_clear_after_input(bool(self.clear_switch.get())),
        )
        self.disable_empty_switch = self.setting_switch(
            content,
            "label.disable_hotkey_when_clipboard_empty",
            self.config["disable_hotkey_when_clipboard_empty"],
            lambda: self.controller.set_disable_hotkey_when_clipboard_empty(bool(self.disable_empty_switch.get())),
        )
        self.ime_switch = self.setting_switch(
            content,
            "label.toggle_ime_with_shift",
            self.config["toggle_ime_with_shift"],
            lambda: self.controller.set_toggle_ime_with_shift(bool(self.ime_switch.get())),
        )
        self.newline_switch = self.setting_switch(
            content,
            "label.newline_with_shift_enter",
            self.config["newline_with_shift_enter"],
            lambda: self.controller.set_newline_with_shift_enter(bool(self.newline_switch.get())),
        )
        self.multi_slot_switch = self.setting_switch(
            content,
            "label.multi_slot_enabled",
            self.config["multi_slot_enabled"],
            lambda: self.controller.set_multi_slot_enabled(bool(self.multi_slot_switch.get())),
        )
        self.close_to_tray_switch = self.setting_switch(
            content,
            "label.close_to_tray",
            self.config["close_to_tray"],
            lambda: self.controller.set_close_to_tray(bool(self.close_to_tray_switch.get())),
        )
        self.startup_switch = self.setting_switch(
            content,
            "label.startup_on_boot",
            self.config["startup_on_boot"],
            lambda: self.controller.set_startup_on_boot(bool(self.startup_switch.get())),
        )
        self.remember_settings_switch = self.setting_switch(
            content,
            "label.remember_settings",
            self.config["remember_settings"],
            lambda: self.controller.set_remember_settings(bool(self.remember_settings_switch.get())),
        )
        self.close_popup_on_blur_switch = self.setting_switch(
            content,
            "label.close_popup_on_blur",
            self.config["close_popup_on_blur"],
            lambda: self.controller.set_close_popup_on_blur(bool(self.close_popup_on_blur_switch.get())),
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
        self.place_settings_window_near_main(win, *self.SETTINGS_SIZE)
        self.register_child_popup(win, self.close_settings)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def open_about(self):
        if self.widget_exists(self.about_window):
            self.center_child_window(self.about_window, self, *self.ABOUT_SIZE)
            self.focus_window_safely(self.about_window)
            return

        self.close_settings()
        self.prune_tooltips()
        win = ctk.CTkToplevel(self)
        self.about_window = win
        self.prepare_popup(win, *self.ABOUT_SIZE)
        frame = self.popup_frame(win)
        self.popup_header(
            frame,
            "label.about_with_product",
            self.close_about,
            actions=[
                ("G", self.controller.open_github, "tooltip.github"),
                ("@", self.controller.copy_email, "tooltip.email"),
            ],
            centered=True,
        )
        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        meta = ctk.CTkFrame(body, fg_color="transparent")
        meta.pack(fill="x", pady=(2, 6))
        ctk.CTkLabel(meta, text=f"{self.t('label.author')}: {self.t('about.author')}", font=("Segoe UI", 11), text_color="#c6ced9").pack(side="left")
        ctk.CTkLabel(meta, text=f"v{APP_VERSION}", font=("Segoe UI", 10), text_color=MUTED).pack(side="right")

        content_text = (
            f"{self.t('about.long_description')}\n\n"
            f"{self.t('about.usage_title')}\n{self.t('help.body')}\n\n"
            f"{self.t('about.notes_title')}\n{self.t('about.notes')}"
        )
        card_width = self.ABOUT_SIZE[0] - 34
        card_height = self.ABOUT_SIZE[1] - 92
        text_canvas = tk.Canvas(
            body,
            width=card_width,
            height=card_height,
            bg="#454a51",
            bd=0,
            highlightthickness=0,
        )
        text_canvas.pack(fill="both", expand=True, pady=(4, 0))
        text_canvas.create_text(
            card_width // 2,
            card_height // 2,
            text=self.t("about.watermark"),
            fill="#596069",
            font=("Microsoft YaHei UI", 32, "bold"),
            angle=-24,
        )
        text_canvas.create_text(
            13,
            13,
            anchor="nw",
            text=content_text,
            width=card_width - 26,
            fill="#f1f3f6",
            font=("Microsoft YaHei UI", 9),
        )
        self.center_child_window(win, self, *self.ABOUT_SIZE)
        self.register_child_popup(win, self.close_about)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def prepare_popup(self, win, width, height):
        win.overrideredirect(True)
        win.resizable(False, False)
        win.attributes("-topmost", bool(self.config["always_on_top"]))
        win.attributes("-alpha", float(self.config["opacity"]))
        self.apply_transparent_background(win)
        win.geometry(f"{width}x{height}")

    def popup_frame(self, win):
        frame = ctk.CTkFrame(win, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=BORDER)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        return frame

    def apply_transparent_background(self, win):
        win.configure(fg_color=TRANSPARENT_KEY)
        try:
            win.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        except Exception:
            win.configure(fg_color=SURFACE)

    def popup_header(self, parent, title_key, close_command, actions=None, centered=False):
        win = parent.winfo_toplevel()
        header = ctk.CTkFrame(parent, fg_color="transparent", height=34)
        header.pack(fill="x", padx=10, pady=(7, 3))
        header.pack_propagate(False)
        title = ctk.CTkLabel(header, text=self.t(title_key), font=("Segoe UI", 13, "bold"), text_color=TEXT)
        if centered:
            title.place(relx=0.5, rely=0.5, anchor="center")
        else:
            title.pack(side="left")
        close_button = self.icon_button(header, "×", close_command, "tooltip.close")
        close_button.pack(side="right")
        for text, command, tooltip_key in reversed(actions or []):
            button = self.icon_button(header, text, command, tooltip_key)
            button.pack(side="right", padx=(0, 3))
        for widget in (header, title):
            widget.bind("<ButtonPress-1>", lambda event, target=win: self.start_popup_drag(target, event), add="+")
            widget.bind("<B1-Motion>", lambda event, target=win: self.drag_popup(target, event), add="+")

    def position_popup(self, win, width, height):
        self.center_child_window(win, self, width, height)

    def place_settings_window_near_main(self, win, width, height):
        if not self.widget_exists(win):
            return
        try:
            self.update_idletasks()
            win.update_idletasks()
            root_x = self.winfo_x()
            root_y = self.winfo_y()
            root_w = self.winfo_width()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            gap = 10
            x = root_x - width - gap
            if x < 0:
                x = root_x + root_w + gap
            if x + width > screen_w:
                x = max(0, screen_w - width - 8)
            y = root_y
            if y < 0:
                y = 0
            if y + height > screen_h:
                y = max(0, screen_h - height - 40)
            win.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            pass

    def position_settings_window(self, win, width, height):
        self.place_settings_window_near_main(win, width, height)

    def center_child_window(self, child, parent, width=None, height=None):
        if not self.widget_exists(child) or not self.widget_exists(parent):
            return
        try:
            parent.update_idletasks()
            child.update_idletasks()
            child_w = width or child.winfo_width() or child.winfo_reqwidth()
            child_h = height or child.winfo_height() or child.winfo_reqheight()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_w = parent.winfo_width()
            parent_h = parent.winfo_height()
            screen_w = parent.winfo_screenwidth()
            screen_h = parent.winfo_screenheight()
            x = parent_x + (parent_w - child_w) // 2
            y = parent_y + (parent_h - child_h) // 2
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x + child_w > screen_w:
                x = max(0, screen_w - child_w - 8)
            if y + child_h > screen_h:
                y = max(0, screen_h - child_h - 40)
            child.geometry(f"{child_w}x{child_h}+{x}+{y}")
        except tk.TclError:
            pass

    def register_child_popup(self, win, close_command):
        if not self.widget_exists(win):
            return
        self.child_popups = [(popup, closer) for popup, closer in self.child_popups if self.widget_exists(popup)]
        self.child_popups.append((win, close_command))
        try:
            win.bind(
                "<FocusOut>",
                lambda _event, popup=win, closer=close_command: self.schedule_child_focus_check(popup, closer),
                add="+",
            )
        except tk.TclError:
            return
        if self.config.get("close_popup_on_blur", True) and self.outside_click_binding is None:
            self.after(80, self.bind_outside_click_close_safely)

    def schedule_child_focus_check(self, win, close_command):
        if not self.widget_exists(win):
            self.forget_child_popup(win)
            return
        try:
            self.after(80, lambda popup=win, closer=close_command: self.close_child_popup_if_unfocused(popup, closer))
        except tk.TclError:
            pass

    def close_child_popup_if_unfocused(self, win, close_command):
        if not self.config.get("close_popup_on_blur", True):
            return
        if not self.widget_exists(win):
            self.forget_child_popup(win)
            return
        try:
            focused = self.focus_get()
        except tk.TclError:
            return
        if focused is not None and self.widget_belongs_to_window(focused, win):
            return
        try:
            pointer_x = self.winfo_pointerx()
            pointer_y = self.winfo_pointery()
        except tk.TclError:
            return
        if self.point_inside_window(pointer_x, pointer_y, win):
            return
        close_command()

    def widget_belongs_to_window(self, widget, win):
        try:
            current = widget
            while current is not None:
                if current is win:
                    return True
                current = getattr(current, "master", None)
        except tk.TclError:
            return False
        return False

    def bind_outside_click_close(self):
        if self.config.get("close_popup_on_blur", True) and self.outside_click_binding is None and self.child_popups:
            try:
                self.outside_click_binding = self.bind("<ButtonPress-1>", self.close_child_popups_on_outside_click, add="+")
            except tk.TclError:
                self.outside_click_binding = None

    def bind_outside_click_close_safely(self):
        if self.widget_exists(self):
            self.bind_outside_click_close()

    def close_child_popups_on_outside_click(self, event):
        if not self.config.get("close_popup_on_blur", True):
            return
        if event.widget in (self.settings_button, self.about_button):
            return
        for popup, close_command in list(self.child_popups):
            if not self.widget_exists(popup):
                self.forget_child_popup(popup)
                continue
            if not self.point_inside_window(event.x_root, event.y_root, popup):
                close_command()

    def point_inside_window(self, x, y, win):
        if not self.widget_exists(win):
            return False
        try:
            return (
                win.winfo_rootx() <= x < win.winfo_rootx() + win.winfo_width()
                and win.winfo_rooty() <= y < win.winfo_rooty() + win.winfo_height()
            )
        except tk.TclError:
            return False

    def forget_child_popup(self, win):
        self.child_popups = [(popup, closer) for popup, closer in self.child_popups if popup is not win and self.widget_exists(popup)]
        if not self.child_popups and self.outside_click_binding is not None:
            try:
                self.unbind("<ButtonPress-1>", self.outside_click_binding)
            except tk.TclError:
                pass
            self.outside_click_binding = None

    def close_settings(self):
        win = self.settings_window
        self.settings_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except tk.TclError:
            pass

    def close_about(self):
        win = self.about_window
        self.about_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except tk.TclError:
            pass

    def dispose_transients(self):
        self.close_settings()
        self.close_about()
        for _button, (_key, tooltip) in list(self.tooltips.items()):
            tooltip.hide()
        self.tooltips.clear()
        self.child_popups.clear()
        if self.outside_click_binding is not None:
            try:
                self.unbind("<ButtonPress-1>", self.outside_click_binding)
            except tk.TclError:
                pass
            self.outside_click_binding = None

    def setting_entry(self, parent, value):
        entry = ctk.CTkEntry(
            parent,
            height=25,
            corner_radius=6,
            border_color="#303743",
            fg_color=SURFACE_DARK,
            text_color=TEXT,
            font=("Segoe UI", 10),
        )
        entry.insert(0, value)
        return entry

    def setting_row(self, parent, label_key, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=self.t(label_key), width=88, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
        entry = self.setting_entry(row, value)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def setting_switch(self, parent, label_key, value, command):
        switch = ctk.CTkSwitch(
            parent,
            text=self.t(label_key),
            switch_width=30,
            switch_height=16,
            progress_color=ACCENT,
            button_color="#dce4ee",
            font=("Segoe UI", 10),
            command=command,
        )
        switch.pack(anchor="w", pady=4)
        if value:
            switch.select()
        return switch

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

    def start_drag(self, event):
        self.drag_x = event.x_root - self.winfo_x()
        self.drag_y = event.y_root - self.winfo_y()

    def drag_window(self, event):
        self.geometry(f"+{event.x_root - self.drag_x}+{event.y_root - self.drag_y}")

    def start_popup_drag(self, win, event):
        if not self.widget_exists(win):
            return
        try:
            self.popup_drag_x = event.x_root - win.winfo_x()
            self.popup_drag_y = event.y_root - win.winfo_y()
        except tk.TclError:
            pass

    def drag_popup(self, win, event):
        if not self.widget_exists(win):
            return
        try:
            win.geometry(f"+{event.x_root - self.popup_drag_x}+{event.y_root - self.popup_drag_y}")
        except tk.TclError:
            pass

    def minimize_window(self):
        self.overrideredirect(False)
        self.iconify()
        self.map_binding = self.bind("<Map>", self.restore_borderless, add="+")

    def restore_borderless(self, _event=None):
        try:
            self.after(10, self.restore_borderless_safely)
        except tk.TclError:
            pass
        if self.map_binding:
            try:
                self.unbind("<Map>", self.map_binding)
            except tk.TclError:
                pass
            self.map_binding = None

    def restore_borderless_safely(self):
        if not self.widget_exists(self):
            return
        try:
            self.overrideredirect(True)
        except tk.TclError:
            pass

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
        self.status_label.configure(text=text, text_color=colors.get(state, MUTED))
        if self.widget_exists(getattr(self, "settings_status", None)):
            self.settings_status.configure(text=text, text_color=colors.get(state, MUTED))

    def set_clipboard_switch(self, enabled):
        if enabled:
            self.listen_switch.select()
            if self.widget_exists(getattr(self, "clipboard_switch", None)):
                self.clipboard_switch.select()
        else:
            self.listen_switch.deselect()
            if self.widget_exists(getattr(self, "clipboard_switch", None)):
                self.clipboard_switch.deselect()

    def set_hotkeys_switch(self, enabled):
        if enabled:
            self.hotkeys_switch.select()
        else:
            self.hotkeys_switch.deselect()

    def set_disable_empty_switch(self, enabled):
        if self.widget_exists(getattr(self, "disable_empty_switch", None)):
            self.disable_empty_switch.select() if enabled else self.disable_empty_switch.deselect()

    def set_ime_switch(self, enabled):
        if self.widget_exists(getattr(self, "ime_switch", None)):
            self.ime_switch.select() if enabled else self.ime_switch.deselect()

    def set_newline_switch(self, enabled):
        if self.widget_exists(getattr(self, "newline_switch", None)):
            self.newline_switch.select() if enabled else self.newline_switch.deselect()

    def set_multi_slot_switch(self, enabled):
        if self.widget_exists(getattr(self, "multi_slot_switch", None)):
            self.multi_slot_switch.select() if enabled else self.multi_slot_switch.deselect()

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
        if self.config.get("close_popup_on_blur", True):
            if self.child_popups and self.outside_click_binding is None:
                self.bind_outside_click_close()
            return
        if self.outside_click_binding is not None:
            self.unbind("<ButtonPress-1>", self.outside_click_binding)
            self.outside_click_binding = None

    def set_multi_slot_visible(self, enabled):
        self.update_multi_slot_visibility(enabled)

    def update_multi_slot_visibility(self, enabled):
        self.set_multi_slot_switch(enabled)
        self.is_multi_slot_visible = bool(enabled)
        if self.is_multi_slot_visible:
            self.rebuild_multi_slot_frame()
            self.multi_slot_frame.pack(fill="x", padx=12, pady=(0, 6), before=self.action_frame)
        else:
            self.destroy_multi_slot_frame()
        self.rebuild_layout()

    def rebuild_layout(self):
        target_height = self.EXPANDED_HEIGHT if self.is_multi_slot_visible else self.HEIGHT
        x = self.winfo_x()
        y = self.winfo_y()
        self.geometry(f"{self.WIDTH}x{target_height}+{x}+{y}")
        self.update_idletasks()

    def rebuild_multi_slot_frame(self):
        self.destroy_multi_slot_frame()
        self.multi_slot_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color=PANEL,
            corner_radius=9,
            border_width=1,
            border_color=BORDER,
            height=self.SLOT_FRAME_HEIGHT,
        )
        self.slot_entries = []
        for index, label in enumerate([self.t(f"label.slot_{slot}") for slot in (1, 2, 3, 4, 5, 6, 7, 8, 9, 0)]):
            row = ctk.CTkFrame(self.multi_slot_frame, fg_color="transparent", height=34)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=label, width=46, anchor="w", font=("Segoe UI", 10), text_color="#c6ced9").pack(side="left")
            entry = ctk.CTkTextbox(
                row,
                height=self.SLOT_TEXTBOX_HEIGHT,
                corner_radius=6,
                border_width=1,
                border_color="#303743",
                fg_color=SURFACE_DARK,
                text_color=TEXT,
                font=("Segoe UI", 10),
                wrap="word",
            )
            entry.insert("1.0", self.config["multi_slots"][index] if index < len(self.config["multi_slots"]) else "")
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda _event, slot_index=index, slot_entry=entry: self.controller.update_multi_slot(slot_index, slot_entry.get("1.0", "end-1c")), add="+")
            entry.bind("<FocusOut>", lambda _event, slot_index=index, slot_entry=entry: self.controller.update_multi_slot(slot_index, slot_entry.get("1.0", "end-1c")), add="+")
            self.slot_entries.append(entry)

    def destroy_multi_slot_frame(self):
        if self.widget_exists(self.multi_slot_frame):
            self.multi_slot_frame.pack_forget()
            self.multi_slot_frame.destroy()
        self.multi_slot_frame = None
        self.slot_entries = []

    def set_startup_switch(self, enabled):
        if self.widget_exists(getattr(self, "startup_switch", None)):
            self.startup_switch.select() if enabled else self.startup_switch.deselect()

    def set_close_to_tray_switch(self, enabled):
        if self.widget_exists(getattr(self, "close_to_tray_switch", None)):
            self.close_to_tray_switch.select() if enabled else self.close_to_tray_switch.deselect()

    def set_opacity_value(self, value):
        alpha = float(value)
        self.attributes("-alpha", alpha)
        for win in (self.settings_window, self.about_window):
            if self.widget_exists(win):
                win.attributes("-alpha", alpha)

    def set_topmost_value(self, enabled):
        self.attributes("-topmost", bool(enabled))
        for win in (self.settings_window, self.about_window):
            if self.widget_exists(win):
                win.attributes("-topmost", bool(enabled))
        self.update_pin_button(enabled)

    def update_pin_button(self, enabled):
        self.pin_button.configure(text="📌", text_color="#6fb49d" if enabled else "#c7d0dc")

    def show_warning(self, _title, message):
        self.set_status(message, "error")

    def reset_input_progress(self):
        self.progress_bar.set(0)
        self.progress_percent_label.configure(text="")

    def set_input_progress(self, done, total):
        if total <= 0:
            self.progress_bar.set(0)
            self.progress_percent_label.configure(text="")
            return
        ratio = min(max(done / total, 0), 1)
        self.progress_bar.set(ratio)
        percent = ratio * 100
        if percent <= 0:
            text = ""
        elif percent >= 99.95:
            text = "100%"
        else:
            text = f"{percent:.1f}%"
        self.progress_percent_label.configure(text=text)

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

    def replace_entry_text(self, entry, text):
        entry.delete(0, "end")
        entry.insert(0, text)

    def replace_textbox_text(self, textbox, text):
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)

    def widget_exists(self, widget):
        return widget_exists(widget)
