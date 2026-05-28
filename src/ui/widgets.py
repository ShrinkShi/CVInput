from pathlib import Path

import customtkinter as ctk
from PIL import Image

from .assets import resource_path
from .theme import ACCENT, SURFACE, SURFACE_DARK, TEXT
from .tooltip import Tooltip
from .window_utils import widget_exists


class WidgetFactoryMixin:
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
        hover_font = self.enlarged_font(font)

        def on_enter(_event=None):
            if not self.widget_exists(button):
                return
            button._normal_text_color = button.cget("text_color")
            try:
                button.configure(font=hover_font, text_color=self.icon_hover_color(button._normal_text_color))
                if hover_image is not None:
                    button.configure(image=hover_image)
                elif image is not None:
                    image.configure(size=(18, 18))
            except Exception:
                pass

        def on_leave(_event=None):
            if not self.widget_exists(button):
                return
            try:
                button.configure(font=font, text_color=getattr(button, "_normal_text_color", text_color))
                if hover_image is not None:
                    button.configure(image=image)
                elif image is not None:
                    image.configure(size=(16, 16))
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

    def widget_exists(self, widget):
        return widget_exists(widget)
