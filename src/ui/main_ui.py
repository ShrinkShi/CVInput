import customtkinter as ctk

from ..constants import APP_NAME
from ..debug_logger import debug_log
from .about_mixin import AboutMixin
from .main_manager import MainManagerMixin
from .settings_mixin import SettingsMixin
from .slot_mixin import SlotMixin
from .theme import ACCENT, BORDER, MUTED, SURFACE, SURFACE_DARK, TEXT
from .widgets import WidgetFactoryMixin
from .window_mixin import WindowMixin


class CVInputUI(
    WidgetFactoryMixin,
    WindowMixin,
    SettingsMixin,
    AboutMixin,
    SlotMixin,
    MainManagerMixin,
    ctk.CTk,
):
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
        self.settings_icon_hover = self.load_icon("set.png", size=(18, 18), tint="#6fb49d")
        self.about_icon = self.load_icon("about.png")
        self.about_icon_hover = self.load_icon("about.png", size=(18, 18), tint="#6fb49d")
        self.github_icon = self.load_icon("github.png")
        self.github_icon_hover = self.load_icon("github.png", size=(18, 18), tint="#6fb49d")
        self.email_icon = self.load_icon("email.png")
        self.email_icon_hover = self.load_icon("email.png", size=(18, 18), tint="#6fb49d")

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
        self.after_idle(self.debug_initial_window_metrics)

    def t(self, key, **kwargs):
        return self.controller.t(key, **kwargs)

    def debug_initial_window_metrics(self):
        try:
            self.update_idletasks()
            debug_log(
                "WINDOW",
                "main_window_initialized",
                geometry=self.geometry(),
                winfo_x=self.winfo_x(),
                winfo_y=self.winfo_y(),
                winfo_rootx=self.winfo_rootx(),
                winfo_rooty=self.winfo_rooty(),
                winfo_width=self.winfo_width(),
                winfo_height=self.winfo_height(),
                winfo_screenwidth=self.winfo_screenwidth(),
                winfo_screenheight=self.winfo_screenheight(),
            )
        except Exception as exc:
            debug_log("WINDOW", "main_window_initialized.error", error=repr(exc))

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
            hover_image=self.settings_icon_hover,
        )
        self.settings_button.pack(side="left")
        self.about_button = self.icon_button(
            self.left_tools,
            "" if self.about_icon else "ⓘ",
            self.open_about,
            "tooltip.about",
            image=self.about_icon,
            hover_image=self.about_icon_hover,
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
            "✏️",
            self.controller.start_typing_from_button,
            "tooltip.type",
            text_color="#6fb49d",
            font=("Segoe UI Emoji", 13),
        )
        self.input_button.pack(side="left", pady=(2, 0))
        self.stop_button = self.icon_button(
            self.action_frame,
            "■",
            self.controller.stop_typing,
            "tooltip.stop",
            text_color="#d47d7d",
        )
        self.stop_button.pack(side="left", padx=(3, 0), pady=(2, 0))
        self.read_button = self.icon_button(
            self.action_frame,
            "📄",
            self.controller.read_clipboard_now,
            "tooltip.read_clipboard",
            font=("Segoe UI Emoji", 13),
        )
        self.read_button.pack(side="left", padx=(3, 0), pady=(2, 0))
        self.progress_bar = ctk.CTkProgressBar(
            self.action_frame,
            width=78,
            height=5,
            corner_radius=4,
            fg_color="#242a33",
            progress_color="#6fb49d",
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=(8, 0), pady=(8, 0))
        self.progress_percent_label = ctk.CTkLabel(
            self.action_frame,
            text="",
            width=38,
            anchor="w",
            font=("Segoe UI", 9),
            text_color=MUTED,
        )
        self.progress_percent_label.pack(side="left", padx=(5, 0), pady=(1, 0))

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
        self.add_tooltip(self.hotkeys_switch, "tooltip.hotkeys_switch")
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
        self.add_tooltip(self.listen_switch, "tooltip.listen_switch")
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


__all__ = ["CVInputUI"]
