import threading

from ..clipboard import ClipboardMonitor
from ..config import ConfigStore
from ..constants import APP_NAME
from ..hotkey import HotkeyManager
from ..i18n import Translator
from ..startup import StartupManager
from ..tray import TrayManager
from ..typing_engine import TypingEngine
from ..ui.main_ui import CVInputUI
from .clipboard_controller import ClipboardController
from .hotkey_controller import HotkeyController
from .lifecycle import LifecycleController
from .settings_controller import SettingsController
from .tray_controller import TrayController
from .typing_controller import TypingController


class CVInputApp(
    LifecycleController,
    HotkeyController,
    ClipboardController,
    TypingController,
    SettingsController,
    TrayController,
):
    def __init__(self):
        self.config_store = ConfigStore()
        self.config = self.config_store.load()
        self.ensure_multi_slots()
        self.translator = Translator(self.config["language"])

        self.ui = CVInputUI(self, self.config)
        self.main_hotkey_manager = HotkeyManager()
        self.slot_hotkey_manager = HotkeyManager(base_id=100)
        self.toggle_hotkey_manager = HotkeyManager(base_id=200)
        self.main_hotkey_registered = False
        self.registered_main_hotkey = None
        self.slot_hotkeys_active = False
        self.toggle_hotkey_registered = False
        self.registered_toggle_hotkey = None
        self.clipboard_monitor = ClipboardMonitor(self.schedule_clipboard_update)
        self.typing_engine = TypingEngine()
        self.startup_manager = StartupManager()
        self.tray_manager = TrayManager(
            APP_NAME,
            self.t,
            self.request_activate_window,
            self.request_toggle_window,
            self.request_exit,
        )
        self.typing_stop_event = threading.Event()
        self.typing_thread = None
        self.exiting = False

        self.clipboard_monitor.set_enabled(bool(self.config["auto_clipboard"]))
        self.clipboard_monitor.start()
        self.tray_manager.start()
        self.register_hotkey()

    def t(self, key, **kwargs):
        return self.translator.t(key, **kwargs)

    def run(self):
        self.ui.mainloop()

    def save_config(self):
        self.config_store.save(self.config)
