import tkinter as tk

import customtkinter as ctk

from .theme import TRANSPARENT_KEY
from .window_utils import widget_exists


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
