import threading
import sys
from pathlib import Path

import pystray
from PIL import Image, ImageDraw


class TrayManager:
    def __init__(self, app_name, labels, on_activate_window, on_toggle_window, on_exit):
        self.app_name = app_name
        self.labels = labels
        self.on_activate_window = on_activate_window
        self.on_toggle_window = on_toggle_window
        self.on_exit = on_exit
        self.icon = None
        self.thread = None

    def start(self):
        if self.icon:
            return
        self.icon = pystray.Icon(self.app_name, self.load_icon(), self.app_name, self.build_menu())
        self.thread = threading.Thread(target=self.icon.run, daemon=True)
        self.thread.start()

    def stop(self):
        if self.icon:
            self.icon.stop()
            self.icon = None

    def refresh_menu(self):
        if not self.icon:
            return
        self.icon.menu = self.build_menu()
        try:
            self.icon.update_menu()
        except Exception:
            pass

    def build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(self.app_name, self._activate_window, default=True, visible=False),
            pystray.MenuItem(self.labels("tray.show_hide"), self._toggle_window),
            pystray.MenuItem(self.labels("tray.exit"), self._exit),
        )

    def _activate_window(self, _icon, _item):
        self.on_activate_window()

    def _toggle_window(self, _icon, _item):
        self.on_toggle_window()

    def _exit(self, _icon, _item):
        self.on_exit()

    def load_icon(self):
        icon_path = self.resource_path("assets/icon.ico")
        try:
            return Image.open(icon_path)
        except Exception:
            image = Image.new("RGBA", (64, 64), (27, 31, 37, 255))
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(66, 109, 100, 255))
            draw.text((22, 20), "CV", fill=(238, 244, 242, 255))
            return image

    def resource_path(self, relative_path):
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / relative_path
        return Path(__file__).resolve().parent.parent / relative_path
