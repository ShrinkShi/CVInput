import tkinter as tk

from ..debug_logger import debug_log
from .theme import MUTED


class MainManagerMixin:
    def refresh_texts(self, rebuild_popups=True):
        self.title_label.configure(text=self.t("app.title"))
        self.subtitle_label.configure(text=self.t("app.subtitle"))
        self.raw_text_label.configure(text=self.t("label.raw_clipboard_text"))
        self.candidate_text_label.configure(text=self.t("label.input_candidate_text"))
        self.listen_switch.configure(text=self.t("label.listen"))
        self.hotkeys_switch.configure(text=self.t("label.hotkeys"))
        for _button, (key, tooltip) in self.tooltips.items():
            tooltip.set_text(self.t(key))
        self.refresh_pin_button_state()
        if rebuild_popups:
            settings_open = self.widget_exists(self.settings_window)
            about_open = self.widget_exists(self.about_window)
            if settings_open:
                self.close_settings()
                self.after(10, self.open_settings)
            if about_open:
                self.close_about()
                self.after(10, self.open_about)

    def start_drag(self, event):
        self._debug_drag_printed = False
        self.drag_x = event.x_root - self.winfo_x()
        self.drag_y = event.y_root - self.winfo_y()
        debug_log(
            "WINDOW_POSITION",
            "start_drag",
            event_x_root=event.x_root,
            event_y_root=event.y_root,
            pointer_x=self.winfo_pointerx(),
            pointer_y=self.winfo_pointery(),
            winfo_x=self.winfo_x(),
            winfo_y=self.winfo_y(),
            geometry=self.geometry(),
            new_x=event.x_root - self.drag_x,
            new_y=event.y_root - self.drag_y,
        )

    def drag_window(self, event):
        new_x = event.x_root - self.drag_x
        new_y = event.y_root - self.drag_y
        if not getattr(self, "_debug_drag_printed", False):
            debug_log(
                "WINDOW_POSITION",
                "drag_window",
                event_x_root=event.x_root,
                event_y_root=event.y_root,
                pointer_x=self.winfo_pointerx(),
                pointer_y=self.winfo_pointery(),
                winfo_x=self.winfo_x(),
                winfo_y=self.winfo_y(),
                geometry=self.geometry(),
                new_x=new_x,
                new_y=new_y,
            )
            self._debug_drag_printed = True
        self.geometry(f"+{new_x}+{new_y}")
        self.update_child_windows_position()

    def minimize_window(self):
        self.close_transient_windows()
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

    def get_raw_text(self):
        return self.raw_text_box.get("1.0", "end-1c")

    def set_raw_text(self, text):
        self.raw_text_box.delete("1.0", "end")
        self.raw_text_box.insert("1.0", text)

    def clear_raw_text(self):
        self.raw_text_box.delete("1.0", "end")

    def is_text_focused(self):
        focused = self.focus_get()
        return focused in (self.text_box, self.raw_text_box)

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

    def set_opacity_value(self, value):
        alpha = float(value)
        self.attributes("-alpha", alpha)
        for win in (self.settings_window, self.about_window, self.developer_debug_window):
            if self.widget_exists(win):
                win.attributes("-alpha", alpha)

    def set_topmost_value(self, enabled):
        self.attributes("-topmost", bool(enabled))
        for win in (self.settings_window, self.about_window, self.developer_debug_window):
            if self.widget_exists(win):
                win.attributes("-topmost", bool(enabled))
        self.update_pin_button(enabled)

    def refresh_pin_button_state(self):
        self.update_pin_button(bool(self.config["always_on_top"]))

    def update_pin_button(self, enabled):
        if not self.widget_exists(getattr(self, "pin_button", None)):
            return
        color = "#6fb49d" if enabled else "#c7d0dc"
        self.pin_button._normal_text_color = color
        self.pin_button.configure(text="📌︎", text_color=color)

    def show_warning(self, _title, message):
        self.set_status(message, "error")

    def reset_input_progress(self):
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=self.progress_color_for_ratio(0))
        self.progress_percent_label.configure(text="")

    def set_input_progress(self, done, total):
        if total <= 0:
            self.progress_bar.set(0)
            self.progress_bar.configure(progress_color=self.progress_color_for_ratio(0))
            self.progress_percent_label.configure(text="")
            return
        ratio = min(max(done / total, 0), 1)
        self.progress_bar.set(ratio)
        self.progress_bar.configure(progress_color=self.progress_color_for_ratio(ratio))
        percent = ratio * 100
        if percent <= 0:
            text = ""
        elif percent >= 99.95:
            text = "100%"
        else:
            text = f"{percent:.1f}%"
        self.progress_percent_label.configure(text=text)

    def progress_color_for_ratio(self, ratio):
        ratio = min(max(float(ratio), 0.0), 1.0)
        if ratio <= 0.5:
            return self.interpolate_color("#d47d7d", "#c7a86a", ratio / 0.5)
        return self.interpolate_color("#c7a86a", "#6fb49d", (ratio - 0.5) / 0.5)

    def interpolate_color(self, start, end, ratio):
        ratio = min(max(float(ratio), 0.0), 1.0)
        start_rgb = self.hex_to_rgb(start)
        end_rgb = self.hex_to_rgb(end)
        mixed = tuple(round(start_rgb[index] + (end_rgb[index] - start_rgb[index]) * ratio) for index in range(3))
        return f"#{mixed[0]:02x}{mixed[1]:02x}{mixed[2]:02x}"

    def hex_to_rgb(self, value):
        value = str(value).lstrip("#")
        return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
