import tkinter as tk

import customtkinter as ctk

from .theme import BORDER, SURFACE, TEXT, TRANSPARENT_KEY
from ..debug_logger import debug_log
from .window_utils import coerce_window_size, developer_panel_geometry, left_attached_geometry, widget_exists


class WindowMixin:
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
            if not getattr(win, "_cvinput_popup_ready", True):
                return
            if win.state() == "withdrawn":
                return
            win.lift()
            win.focus_force()
        except tk.TclError:
            pass

    def prepare_popup(self, win, width, height):
        win._cvinput_popup_ready = False
        win.withdraw()
        win.overrideredirect(True)
        win.resizable(False, False)
        win.minsize(width, height)
        win.maxsize(width, height)
        win.attributes("-topmost", bool(self.config["always_on_top"]))
        win.attributes("-alpha", 0.0)
        self.apply_transparent_background(win)
        win.geometry(f"{width}x{height}+0+0")

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
        for action in reversed(actions or []):
            text, command, tooltip_key = action[:3]
            image = action[3] if len(action) > 3 else None
            hover_image = action[4] if len(action) > 4 else None
            button = self.icon_button(header, "" if image else text, command, tooltip_key, image=image, hover_image=hover_image)
            button.pack(side="right", padx=(0, 3))
        for widget in (header, title):
            widget.bind("<ButtonPress-1>", lambda event, target=win: self.start_popup_drag(target, event), add="+")
            widget.bind("<B1-Motion>", lambda event, target=win: self.drag_popup(target, event), add="+")

    def position_popup(self, win, width, height):
        self.place_child_window_near_main(win, width, height)

    def _apply_child_left_geometry(self, child, width=None, height=None):
        return self._apply_window_left_geometry(self, child, width, height)

    def _apply_window_left_geometry(self, parent, child, width=None, height=None):
        self.update_idletasks()
        parent.update_idletasks()
        child.update_idletasks()
        before_geometry = child.geometry()
        child_w = coerce_window_size(width, child.winfo_width() or child.winfo_reqwidth())
        child_h = coerce_window_size(height, child.winfo_height() or child.winfo_reqheight())
        child_x, child_y = left_attached_geometry(parent, child_w, child_h)
        target_geometry = f"{child_w}x{child_h}+{child_x}+{child_y}"
        debug_log(
            "WINDOW_POSITION",
            "apply_child_left_geometry.before",
            child_state=child.state(),
            child_geometry=before_geometry,
            target_geometry=target_geometry,
        )
        child.geometry(target_geometry)
        child.update_idletasks()
        debug_log(
            "WINDOW_POSITION",
            "apply_child_left_geometry.after",
            child_state=child.state(),
            child_geometry=child.geometry(),
            child_winfo_x=child.winfo_x(),
            child_winfo_y=child.winfo_y(),
            child_winfo_rootx=child.winfo_rootx(),
            child_winfo_rooty=child.winfo_rooty(),
        )
        return child_w, child_h, target_geometry

    def place_child_left_of_main(self, child, width=None, height=None):
        if not self.widget_exists(child):
            return
        try:
            is_first_show = child.state() == "withdrawn"
            if is_first_show:
                self.show_child_popup(child, width, height)
                return
            self._apply_child_left_geometry(child, width, height)
            child.attributes("-alpha", float(self.config["opacity"]))
        except tk.TclError:
            pass

    def show_child_popup(self, child, width=None, height=None):
        if not self.widget_exists(child):
            return
        try:
            child.attributes("-alpha", 0.0)
            self._apply_child_left_geometry(child, width, height)
            if child.state() == "withdrawn":
                child.deiconify()
                child.update_idletasks()

            # Withdrawn Toplevels can report 133x133 on Windows/CTk until mapped.
            # Re-apply after mapping, then reveal on the next event-loop turn.
            self._apply_child_left_geometry(child, width, height)
            self.after(20, lambda target=child, w=width, h=height: self.finish_first_child_show(target, w, h))
        except tk.TclError:
            pass

    def finish_first_child_show(self, child, width=None, height=None):
        if not self.widget_exists(child):
            return
        try:
            self._apply_child_left_geometry(child, width, height)
            child._cvinput_popup_ready = True
            child.lift()
            child.focus_force()
            child.attributes("-alpha", float(self.config["opacity"]))
        except tk.TclError:
            pass

    def place_child_window_near_main(self, win, width, height):
        self.place_child_left_of_main(win, width, height)

    def update_child_windows_position(self):
        if self.widget_exists(self.settings_window):
            self.place_child_window_near_main(self.settings_window, *self.SETTINGS_SIZE)
        if self.widget_exists(self.about_window):
            self.place_child_window_near_main(self.about_window, *self.ABOUT_SIZE)
        if self.widget_exists(getattr(self, "contact_window", None)) and hasattr(self, "place_contact_window"):
            self.place_contact_window()
        if self.widget_exists(getattr(self, "developer_debug_window", None)):
            self.place_developer_debug_window()

    def place_developer_debug_window(self):
        if not self.widget_exists(getattr(self, "developer_debug_window", None)) or not self.widget_exists(self.settings_window):
            return
        try:
            is_first_show = self.developer_debug_window.state() == "withdrawn"
            if is_first_show:
                self.show_developer_popup(self.developer_debug_window, *self.DEVELOPER_DEBUG_SIZE)
                return
            self._apply_developer_geometry(self.developer_debug_window, *self.DEVELOPER_DEBUG_SIZE)
            self.developer_debug_window.attributes("-alpha", float(self.config["opacity"]))
        except tk.TclError:
            pass

    def _apply_developer_geometry(self, child, width=None, height=None):
        self.update_idletasks()
        self.settings_window.update_idletasks()
        child.update_idletasks()
        child_w = coerce_window_size(width, child.winfo_width() or child.winfo_reqwidth())
        child_h = coerce_window_size(height, child.winfo_height() or child.winfo_reqheight())
        child_x, child_y = developer_panel_geometry(
            self,
            self.settings_window,
            child_w,
            child_h,
            self.SETTINGS_SIZE[0],
        )
        target_geometry = f"{child_w}x{child_h}+{child_x}+{child_y}"
        child.geometry(target_geometry)
        child.update_idletasks()
        return child_w, child_h, target_geometry

    def show_developer_popup(self, child, width=None, height=None):
        if not self.widget_exists(child):
            return
        try:
            child.attributes("-alpha", 0.0)
            self._apply_developer_geometry(child, width, height)
            if child.state() == "withdrawn":
                child.deiconify()
                child.update_idletasks()
            self._apply_developer_geometry(child, width, height)
            self.after(20, lambda target=child, w=width, h=height: self.finish_developer_show(target, w, h))
        except tk.TclError:
            pass

    def finish_developer_show(self, child, width=None, height=None):
        if not self.widget_exists(self.settings_window) or not self.widget_exists(child):
            return
        try:
            self._apply_developer_geometry(child, width, height)
            child._cvinput_popup_ready = True
            child.lift()
            child.focus_force()
            child.attributes("-alpha", float(self.config["opacity"]))
        except tk.TclError:
            pass

    def close_transient_windows(self):
        if hasattr(self, "close_developer_debug"):
            self.close_developer_debug()
        self.close_settings()
        self.close_about()

    def place_settings_window_near_main(self, win, width, height):
        self.place_child_window_near_main(win, width, height)

    def position_settings_window(self, win, width, height):
        self.place_child_window_near_main(win, width, height)

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
        if self.config.get("close_popup_on_blur", False) and self.outside_click_binding is None:
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
        if not self.config.get("close_popup_on_blur", False):
            return
        if not self.widget_exists(win):
            self.forget_child_popup(win)
            return
        try:
            focused = self.focus_get()
        except tk.TclError:
            focused = None
        if focused is not None and self.widget_belongs_to_window(focused, win):
            return
        if focused is not None and any(
            self.widget_belongs_to_window(focused, popup) for popup, _closer in self.child_popups if self.widget_exists(popup)
        ):
            return
        close_command()

    def widget_belongs_to_window(self, widget, win):
        try:
            while widget is not None:
                if widget is win:
                    return True
                widget = widget.master
        except Exception:
            return False
        return False

    def bind_outside_click_close(self):
        if self.outside_click_binding is not None:
            return
        try:
            self.outside_click_binding = self.bind("<ButtonPress-1>", self.close_child_popups_on_outside_click, add="+")
        except tk.TclError:
            self.outside_click_binding = None

    def bind_outside_click_close_safely(self):
        if self.widget_exists(self):
            self.bind_outside_click_close()

    def close_child_popups_on_outside_click(self, event):
        if not self.config.get("close_popup_on_blur", False):
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

    def dispose_transients(self):
        self.close_transient_windows()
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
            if win is getattr(self, "settings_window", None):
                self.place_developer_debug_window()
            if win is getattr(self, "about_window", None) and hasattr(self, "place_contact_window"):
                self.place_contact_window()
        except tk.TclError:
            pass
