import tkinter as tk

import customtkinter as ctk

from ..constants import APP_VERSION
from ..debug_logger import debug_log
from .theme import HOVER, MUTED, SURFACE_DARK, TEXT


CONTACT_EMAIL = "1363072460@qq.com"
CONTACT_QQ = "1363072460"


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
                ("@", self.open_contact_popup, "tooltip.email", self.email_icon, self.email_icon_hover),
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
        text_frame = ctk.CTkFrame(body, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, pady=(4, 0))
        text_canvas = tk.Canvas(
            text_frame,
            width=self.ABOUT_SIZE[0] - 52,
            height=self.ABOUT_SIZE[1] - 110,
            bg="#454a51",
            bd=0,
            highlightthickness=0,
            yscrollincrement=20,
        )
        text_scrollbar = ctk.CTkScrollbar(text_frame, orientation="vertical", command=text_canvas.yview)
        text_canvas.configure(yscrollcommand=text_scrollbar.set)
        text_canvas.pack(side="left", fill="both", expand=True)
        text_scrollbar.pack(side="right", fill="y", padx=(6, 0))
        text_canvas.bind(
            "<Configure>",
            lambda _event, canvas=text_canvas, text=content_text: self.draw_about_canvas(canvas, text),
            add="+",
        )
        text_canvas.bind(
            "<MouseWheel>",
            lambda event, canvas=text_canvas: self.scroll_about_canvas(canvas, event),
            add="+",
        )
        text_scrollbar.bind(
            "<MouseWheel>",
            lambda event, canvas=text_canvas: self.scroll_about_canvas(canvas, event),
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
            text_width = max(width - 38, 1)
            canvas.delete("all")
            text_id = canvas.create_text(
                15,
                15,
                anchor="nw",
                text=content_text,
                width=text_width,
                fill="#f1f3f6",
                font=("Microsoft YaHei UI", 10),
            )
            bbox = canvas.bbox(text_id) or (0, 0, width, height)
            content_height = max(height, bbox[3] + 22)
            canvas.delete("all")
            canvas.create_rectangle(0, 0, width, content_height, fill="#353a42", outline="")
            watermark = self.t("about.watermark")
            for row, y in enumerate(range(82, int(content_height) + 160, 178)):
                for x in (width * 0.27, width * 0.75):
                    canvas.create_text(
                        int(x + (row % 2) * 36),
                        int(y),
                        text=watermark,
                        fill="#4d545d",
                        font=("Microsoft YaHei UI", 38, "bold"),
                        angle=-28,
                    )
            canvas.create_rectangle(0, 0, width, content_height, fill="#454b54", outline="", stipple="gray12")
            canvas.create_text(
                15,
                15,
                anchor="nw",
                text=content_text,
                width=text_width,
                fill="#f1f3f6",
                font=("Microsoft YaHei UI", 10),
            )
            canvas.configure(scrollregion=(0, 0, width, content_height))
        except tk.TclError:
            pass

    def scroll_about_canvas(self, canvas, event):
        if not self.widget_exists(canvas):
            return "break"
        try:
            delta = -1 if event.delta > 0 else 1
            canvas.yview_scroll(delta * 3, "units")
        except tk.TclError:
            pass
        return "break"

    def open_contact_popup(self):
        if self.widget_exists(getattr(self, "contact_window", None)):
            self.focus_window_safely(self.contact_window)
            return

        win = ctk.CTkToplevel(self)
        self.contact_window = win
        self.prepare_popup(win, *self.CONTACT_SIZE)
        frame = self.popup_frame(win)
        self.popup_header(frame, "label.contact_me", self.close_contact_popup, centered=True)

        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=(8, 12))
        self.contact_copy_button(
            content,
            f"{self.t('label.contact_email')}: {CONTACT_EMAIL}",
            CONTACT_EMAIL,
            self.t("label.contact_email"),
        ).pack(fill="x", pady=(0, 8))
        self.contact_copy_button(
            content,
            f"{self.t('label.contact_qq')}: {CONTACT_QQ}",
            CONTACT_QQ,
            self.t("label.contact_qq"),
        ).pack(fill="x")

        self.show_contact_popup(win)
        self.register_child_popup(win, self.close_contact_popup)
        self.after(20, lambda target=win: self.focus_window_safely(target))

    def contact_copy_button(self, parent, text, value, item):
        return ctk.CTkButton(
            parent,
            text=text,
            height=30,
            corner_radius=7,
            fg_color=SURFACE_DARK,
            hover_color=HOVER,
            text_color=TEXT,
            anchor="w",
            font=("Segoe UI", 11),
            command=lambda copied=value, label=item: self.controller.copy_contact_text(copied, label),
        )

    def show_contact_popup(self, win):
        if not self.widget_exists(win):
            return
        try:
            win.attributes("-alpha", 0.0)
            self.place_contact_window()
            if win.state() == "withdrawn":
                win.deiconify()
                win.update_idletasks()
            self.place_contact_window()
            self.after(20, lambda target=win: self.finish_contact_popup_show(target))
        except tk.TclError:
            pass

    def finish_contact_popup_show(self, win):
        if not self.widget_exists(win):
            return
        try:
            self.place_contact_window()
            win._cvinput_popup_ready = True
            win.lift()
            win.focus_force()
            win.attributes("-alpha", float(self.config["opacity"]))
        except tk.TclError:
            pass

    def place_contact_window(self):
        if not self.widget_exists(getattr(self, "contact_window", None)):
            return
        parent = self.about_window if self.widget_exists(self.about_window) else self
        self._apply_window_left_geometry(parent, self.contact_window, *self.CONTACT_SIZE)

    def close_contact_popup(self):
        win = getattr(self, "contact_window", None)
        self.contact_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except Exception:
            pass

    def close_about(self):
        self.close_contact_popup()
        win = self.about_window
        self.about_window = None
        self.hide_tooltips_for_window(win)
        if win is not None:
            self.forget_child_popup(win)
        try:
            if self.widget_exists(win):
                win.destroy()
        except Exception:
            pass
