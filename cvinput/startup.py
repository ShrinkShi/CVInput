import sys
from pathlib import Path


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE_NAME = "CVInput"


class StartupManager:
    def __init__(self, value_name=RUN_VALUE_NAME):
        self.value_name = value_name

    def set_enabled(self, enabled):
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                if enabled:
                    winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, self.startup_command())
                else:
                    try:
                        winreg.DeleteValue(key, self.value_name)
                    except FileNotFoundError:
                        pass
            return True, None
        except Exception as e:
            return False, str(e)

    def startup_command(self):
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        main_py = Path(__file__).resolve().parent.parent / "main.py"
        return f'"{sys.executable}" "{main_py}"'
