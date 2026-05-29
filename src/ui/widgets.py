from pathlib import Path
import tkinter as tk

import customtkinter as ctk
from PIL import Image

from .assets import resource_path
from .theme import ACCENT, SURFACE, SURFACE_DARK, TEXT, TRANSPARENT_KEY
from .tooltip import Tooltip
from .window_utils import widget_exists


class WidgetFactoryMixin:
    OPTION_MENU_HOVER = "#3C444A"
    OPTION_MENU_DROPDOWN_BG = "#20252b"

    def load_icon(self, filename, size=(16, 16), tint=None):
        path = resource_path(Path("assets") / filename)
        try:
            image = Image.open(path).convert("RGBA")
        except (FileNotFoundError, OSError):
            return None
        if tint:
            color = tint.lstrip("#")
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            alpha = image.getchannel("A")
            image = Image.new("RGBA", image.size, (r, g, b, 0))
            image.putalpha(alpha)
        return ctk.CTkImage(light_image=image, dark_image=image, size=size)

    def add_tooltip(self, widget, tooltip_key):
        self.tooltips[widget] = (tooltip_key, Tooltip(widget, self.t(tooltip_key)))

    def icon_hover_color(self, current_color):
        if str(current_color).lower() in ("#6fb49d", "#4f947f"):
            return "#4f947f"
        return "#6fb49d"

    def enlarged_font(self, font):
        if isinstance(font, tuple) and len(font) >= 2 and isinstance(font[1], int):
            return (font[0], font[1] + 2, *font[2:])
        return font

    def icon_button(
        self,
        parent,
        text,
        command,
        tooltip_key,
        text_color="#c7d0dc",
        font=("Segoe UI Symbol", 13),
        image=None,
        hover_image=None,
        width=25,
        height=25,
    ):
        button = ctk.CTkButton(
            parent,
            text=text,
            image=image,
            width=width,
            height=height,
            corner_radius=6,
            border_width=0,
            fg_color="transparent",
            hover_color=SURFACE,
            text_color=text_color,
            font=font,
            command=command,
        )
        button._normal_image = image
        button._hover_image = hover_image
        button._normal_text_color = text_color

        def on_enter(_event=None):
            if not self.widget_exists(button):
                return
            try:
                button.configure(
                    image=getattr(button, "_hover_image", None) or getattr(button, "_normal_image", None),
                    text_color=self.icon_hover_color(getattr(button, "_normal_text_color", text_color)),
                )
            except Exception:
                pass

        def on_leave(_event=None):
            if not self.widget_exists(button):
                return
            try:
                button.configure(
                    font=font,
                    image=getattr(button, "_normal_image", image),
                    text_color=getattr(button, "_normal_text_color", text_color),
                )
            except Exception:
                pass

        button.bind("<Enter>", on_enter, add="+")
        button.bind("<Leave>", on_leave, add="+")
        self.add_tooltip(button, tooltip_key)
        return button

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

    def setting_switch(self, parent, label_key, value, command, tooltip_key=None):
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
        if tooltip_key:
            self.add_tooltip(switch, tooltip_key)
        return switch

    def replace_entry_text(self, entry, text):
        entry.delete(0, "end")
        entry.insert(0, text)

    def replace_textbox_text(self, textbox, text):
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)

    def apply_app_icon(self, win, schedule_refresh=True):
        # CustomTkinter schedules its own default Windows icon shortly after
        # window creation. Marking this flag prevents that blue CTk icon from
        # replacing our runtime icon.
        try:
            win._iconbitmap_method_called = True
        except Exception:
            pass

        icon_path = resource_path("icon.ico")
        if icon_path.exists():
            try:
                win.iconbitmap(default=str(icon_path))
                win.iconbitmap(str(icon_path))
                win._iconbitmap_method_called = True
            except Exception:
                pass

        photos = []
        for size in (512, 256):
            png_path = resource_path(Path("assets") / "icon" / f"icon{size}.png")
            try:
                photos.append(tk.PhotoImage(file=str(png_path)))
            except Exception:
                pass
        if photos:
            try:
                win._cvinput_icon_photos = photos
                win.iconphoto(True, *photos)
                win.wm_iconphoto(True, *photos)
            except Exception:
                pass
        if schedule_refresh and not getattr(win, "_cvinput_icon_refresh_scheduled", False):
            win._cvinput_icon_refresh_scheduled = True
            for delay in (260, 800):
                try:
                    win.after(delay, lambda target=win: self.apply_app_icon(target, schedule_refresh=False))
                except Exception:
                    pass

    def enable_option_menu_toggle(self, menu):
        if getattr(menu, "_cvinput_toggle_enabled", False):
            return menu

        menu._cvinput_toggle_enabled = True
        menu._cvinput_dropdown_open = False
        menu._cvinput_custom_dropdown = None
        self.style_option_menu(menu)
        original_dropdown_callback = menu._dropdown_callback

        def is_dropdown_mapped():
            custom_dropdown = getattr(menu, "_cvinput_custom_dropdown", None)
            if self.widget_exists(custom_dropdown):
                return True
            dropdown = getattr(menu, "_dropdown_menu", None)
            if dropdown is None:
                return False
            try:
                return bool(dropdown.winfo_ismapped())
            except Exception:
                return False

        def close_dropdown():
            self.close_custom_option_dropdown(menu)
            dropdown = getattr(menu, "_dropdown_menu", None)
            if dropdown is not None:
                try:
                    dropdown.unpost()
                except Exception:
                    pass
            menu._cvinput_dropdown_open = False

        def monitor_dropdown_closed():
            if not self.widget_exists(menu):
                return
            if is_dropdown_mapped():
                try:
                    menu.after(80, monitor_dropdown_closed)
                except Exception:
                    pass
                return
            menu._cvinput_dropdown_open = False

        def clicked(event=0):
            if str(getattr(menu, "_state", "normal")) == "disabled" or not getattr(menu, "_values", []):
                return
            if getattr(menu, "_cvinput_dropdown_open", False):
                close_dropdown()
                return
            menu._cvinput_dropdown_open = True
            self.style_option_menu(menu)
            self.open_custom_option_dropdown(menu, original_dropdown_callback)
            try:
                menu.after(1, lambda target=menu: self.style_option_menu(target))
            except Exception:
                pass
            try:
                menu.after(80, monitor_dropdown_closed)
            except Exception:
                pass

        def dropdown_callback(value):
            menu._cvinput_dropdown_open = False
            self.close_custom_option_dropdown(menu)
            original_dropdown_callback(value)

        menu._clicked = clicked
        try:
            menu._dropdown_menu.configure(command=dropdown_callback)
            menu._create_bindings(sequence="<Button-1>")
        except Exception:
            pass
        return menu

    def open_custom_option_dropdown(self, menu, callback):
        self.close_custom_option_dropdown(menu)
        values = list(getattr(menu, "_values", []) or [])
        if not values:
            menu._cvinput_dropdown_open = False
            return

        try:
            root = menu.winfo_toplevel()
            popup = tk.Toplevel(root)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.configure(bg=TRANSPARENT_KEY)
            try:
                popup.attributes("-transparentcolor", TRANSPARENT_KEY)
            except Exception:
                popup.configure(bg=self.OPTION_MENU_DROPDOWN_BG)
            try:
                popup.attributes("-topmost", bool(root.attributes("-topmost")))
            except Exception:
                popup.attributes("-topmost", True)
        except Exception:
            menu._cvinput_dropdown_open = False
            return

        try:
            widget_scaling = max(float(menu._get_widget_scaling()), 1.0)
        except Exception:
            widget_scaling = 1.0

        def to_logical(value):
            return max(1, int(round(float(value) / widget_scaling)))

        def to_physical(value):
            return max(1, int(round(float(value) * widget_scaling)))

        button_height = 30
        row_gap = 2
        padding = 6
        width = max(to_logical(menu.winfo_width()), 150)
        width += 2
        height = padding * 2 + (button_height + row_gap) * len(values) + 2
        total_w = to_physical(width)
        total_h = to_physical(height)

        frame = ctk.CTkFrame(
            popup,
            width=width,
            height=height,
            fg_color=self.OPTION_MENU_DROPDOWN_BG,
            corner_radius=9,
            border_width=0,
        )
        frame.place(x=0, y=0)

        def select(value):
            self.close_custom_option_dropdown(menu)
            callback(value)

        for value in values:
            button = ctk.CTkButton(
                frame,
                text=value,
                height=button_height,
                corner_radius=7,
                border_width=0,
                fg_color="transparent",
                hover_color=self.OPTION_MENU_HOVER,
                text_color=TEXT,
                font=("Segoe UI", 10),
                anchor="w",
                command=lambda item=value: select(item),
            )
            button.pack(fill="x", padx=padding, pady=(0, row_gap))

        x = int(menu.winfo_rootx())
        y = int(menu.winfo_rooty() + menu.winfo_height() + 4)
        screen_w = int(menu.winfo_screenwidth())
        screen_h = int(menu.winfo_screenheight())
        if x + total_w > screen_w:
            x = max(0, screen_w - total_w - 2)
        if y + total_h > screen_h:
            y = max(0, int(menu.winfo_rooty()) - total_h - 4)

        popup.geometry(f"{total_w}x{total_h}+{x}+{y}")

        def close_if_outside(event=None):
            if event is not None:
                try:
                    left = int(popup.winfo_rootx())
                    top = int(popup.winfo_rooty())
                    right = left + int(popup.winfo_width())
                    bottom = top + int(popup.winfo_height())
                    if left <= int(event.x_root) <= right and top <= int(event.y_root) <= bottom:
                        return
                except Exception:
                    pass
            self.close_custom_option_dropdown(menu)

        def close_if_focus_left():
            if not self.widget_exists(popup):
                return
            try:
                focus = popup.focus_get()
                if focus is not None and str(focus).startswith(str(popup)):
                    return
            except Exception:
                pass
            self.close_custom_option_dropdown(menu)

        popup.bind("<Escape>", lambda _event=None: self.close_custom_option_dropdown(menu), add="+")
        popup.bind("<FocusOut>", lambda _event=None: popup.after(80, close_if_focus_left), add="+")
        popup.bind("<ButtonPress-1>", close_if_outside, add="+")

        menu._cvinput_custom_dropdown = popup
        popup.deiconify()
        popup.lift()
        try:
            popup.focus_force()
            popup.grab_set()
        except Exception:
            pass

    def close_custom_option_dropdown(self, menu):
        popup = getattr(menu, "_cvinput_custom_dropdown", None)
        menu._cvinput_custom_dropdown = None
        menu._cvinput_dropdown_open = False
        if not self.widget_exists(popup):
            return
        try:
            popup.grab_release()
        except Exception:
            pass
        try:
            popup.destroy()
        except Exception:
            pass

    def style_option_menu(self, menu):
        if not self.widget_exists(menu):
            return
        try:
            menu.configure(
                corner_radius=8,
                fg_color=SURFACE_DARK,
                button_color=ACCENT,
                button_hover_color=self.OPTION_MENU_HOVER,
                dropdown_fg_color=self.OPTION_MENU_DROPDOWN_BG,
                dropdown_hover_color=self.OPTION_MENU_HOVER,
                dropdown_text_color=TEXT,
            )
        except Exception:
            pass
        try:
            menu._text_label.configure(borderwidth=0, highlightthickness=0)
        except Exception:
            pass

        dropdown = getattr(menu, "_dropdown_menu", None)
        if dropdown is None:
            return
        try:
            dropdown.configure(
                relief="flat",
                bd=0,
                borderwidth=0,
                activeborderwidth=0,
                bg=self.OPTION_MENU_DROPDOWN_BG,
                fg=TEXT,
                activebackground=self.OPTION_MENU_HOVER,
                activeforeground=TEXT,
                selectcolor=self.OPTION_MENU_HOVER,
            )
        except Exception:
            pass

    def widget_exists(self, widget):
        return widget_exists(widget)
