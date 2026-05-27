import tkinter as tk

import customtkinter as ctk

from ..constants import APP_VERSION
from ..debug_logger import debug_log
from .theme import MUTED


class AboutMixin:
    def open_about(self):
        if self.widget_exists(self.about_window):
            self.close_about()
            return

        self.close_settings()
        self.prune_tooltips()
        debug_log(
            "WINDOW_POSITION",
            "open_about",
            popup_type="about",
            target_width=self.ABOUT_SIZE[0],
            target_height=self.ABOUT_SIZE[1],
        )
        win = ctk.CTkToplevel(self)
        self.about_window = win
        self.prepare_popup(win, *self.ABOUT_SIZE)
        frame = self.popup_frame(win)
        self.popup_header(
            frame,
            "label.about_with_product",
            self.close_about,
            actions=[
                ("G", self.controller.open_github, "tooltip.github", self.github_icon, self.github_icon_hover),
                ("@", self.controller.copy_email, "tooltip.email", self.email_icon, self.email_icon_hover),
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
        text_canvas = tk.Canvas(
            body,
            width=self.ABOUT_SIZE[0] - 34,
            height=self.ABOUT_SIZE[1] - 110,
            bg="#454a51",
            bd=0,
            highlightthickness=0,
        )
        text_canvas.pack(fill="both", expand=True, pady=(4, 0))
        text_canvas.bind(
            "<Configure>",
            lambda event, canvas=text_canvas, text=content_text: self.draw_about_canvas(canvas, text),
            add="+",
        )
        self.after(20, lambda canvas=text_canvas, text=content_text: self.draw_about_canvas(canvas, text))
        self.place_child_window_near_main(win, *self.ABOUT_SIZE)
        self.register_child_popup(win, self.close_about)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def draw_about_canvas(self, canvas, content_text):
        if not self.widget_exists(canvas):
            return
        try:
            width = max(canvas.winfo_width(), 1)
            height = max(canvas.winfo_height(), 1)
            canvas.delete("all")
            canvas.create_rectangle(0, 0, width, height, fill="#353a42", outline="")
            watermark = self.t("about.watermark")
            for x, y in (
                (width * 0.22, height * 0.16),
                (width * 0.70, height * 0.30),
                (width * 0.34, height * 0.54),
                (width * 0.82, height * 0.72),
                (width * 0.20, height * 0.88),
            ):
                canvas.create_text(
                    int(x),
                    int(y),
                    text=watermark,
                    fill="#4d545d",
                    font=("Microsoft YaHei UI", 38, "bold"),
                    angle=-28,
                )
            canvas.create_rectangle(0, 0, width, height, fill="#454b54", outline="", stipple="gray12")
            canvas.create_text(
                13,
                13,
                anchor="nw",
                text=content_text,
                width=max(width - 26, 1),
                fill="#f1f3f6",
                font=("Microsoft YaHei UI", 9),
            )
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
