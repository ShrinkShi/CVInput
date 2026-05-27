class LifecycleController:
    def schedule_ui(self, callback):
        if self.exiting or not self.ui.widget_exists(self.ui):
            return

        def run_if_alive():
            if not self.exiting and self.ui.widget_exists(self.ui):
                callback()

        try:
            self.ui.after(0, run_if_alive)
        except Exception:
            pass

    def close(self):
        if self.config["close_to_tray"] and not self.exiting:
            self.hide_window()
            self.ui.set_status(self.t("status.window_hidden"), "ready")
            return
        self.exit_app()

    def exit_app(self):
        if self.exiting:
            return
        self.exiting = True
        self.typing_stop_event.set()
        self.clipboard_monitor.stop()
        self.main_hotkey_manager.stop()
        self.slot_hotkey_manager.stop()
        self.toggle_hotkey_manager.stop()
        self.tray_manager.stop()
        self.save_config()
        self.ui.dispose_transients()
        self.ui.destroy()
