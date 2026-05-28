class TrayController:
    def request_toggle_window(self):
        self.schedule_ui(self.toggle_window_visibility)

    def request_activate_window(self):
        self.schedule_ui(self.activate_window_from_tray)

    def request_exit(self):
        self.schedule_ui(self.exit_app)

    def toggle_window_visibility(self):
        if self.ui.state() == "withdrawn":
            self.show_window()
        else:
            self.hide_window()

    def show_window(self):
        if self.exiting or not self.ui.widget_exists(self.ui):
            return
        try:
            self.ui.deiconify()
            self.ui.after(10, self.ui.restore_borderless_safely)
            self.ui.lift()
            self.ui.focus_force()
        except Exception:
            pass

    def activate_window_from_tray(self):
        if self.exiting or not self.ui.widget_exists(self.ui):
            return
        if self.ui.state() == "withdrawn":
            self.show_window()
            return
        try:
            self.ui.lift()
            self.ui.focus_force()
        except Exception:
            pass

    def hide_window(self):
        if not self.ui.widget_exists(self.ui):
            return
        try:
            self.ui.close_transient_windows()
            self.ui.withdraw()
        except Exception:
            pass
