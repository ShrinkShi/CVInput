import ctypes
import queue
import threading
from ctypes import wintypes

from pynput.keyboard import Key

from .constants import (
    HOTKEY_ID,
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    MOD_WIN,
    WM_HOTKEY,
    WM_QUIT,
)


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


class HotkeyManager:
    MODIFIER_ALIASES = {
        "ctrl": MOD_CONTROL,
        "control": MOD_CONTROL,
        "alt": MOD_ALT,
        "shift": MOD_SHIFT,
        "win": MOD_WIN,
        "windows": MOD_WIN,
        "meta": MOD_WIN,
    }

    VK_NAMES = {
        "enter": 0x0D,
        "tab": 0x09,
        "space": 0x20,
        "esc": 0x1B,
        "escape": 0x1B,
        "home": 0x24,
        "end": 0x23,
        "pageup": 0x21,
        "pagedown": 0x22,
        "delete": 0x2E,
        "del": 0x2E,
        "backspace": 0x08,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
    }

    def __init__(self):
        self.thread = None
        self.thread_id = None
        self.stop_event = threading.Event()
        self.callback = None
        self.current_hotkey = None
        self.release_keys = []
        self._registered = False

    def parse_hotkey(self, text):
        parts = [part.strip() for part in text.split("+") if part.strip()]
        if not parts:
            raise ValueError("快捷键不能为空")

        modifiers = MOD_NOREPEAT
        release_keys = []
        main_key = None
        main_name = None

        for part in parts:
            token = part.lower()
            if token in self.MODIFIER_ALIASES:
                mod = self.MODIFIER_ALIASES[token]
                modifiers |= mod
                release_keys.extend(self._modifier_release_keys(mod))
                continue
            if main_key is not None:
                raise ValueError("只能设置一个主键")
            main_key = self._parse_main_key(token)
            main_name = token

        if main_key is None:
            raise ValueError("缺少主键")

        release_keys.extend(self._main_release_keys(main_name))
        return modifiers, main_key, release_keys

    def start(self, hotkey_config, callback):
        self.stop()
        try:
            modifiers, vk_code, release_keys = self.parse_hotkey(hotkey_config)
        except ValueError as e:
            return False, str(e)

        self.stop_event.clear()
        self.callback = callback
        self.current_hotkey = hotkey_config
        self.release_keys = release_keys
        result_queue = queue.Queue(maxsize=1)
        self.thread = threading.Thread(
            target=self.hotkey_listener_loop,
            args=(modifiers, vk_code, result_queue),
            daemon=True,
        )
        self.thread.start()

        try:
            ok, message = result_queue.get(timeout=1.5)
        except queue.Empty:
            return False, "快捷键注册超时"
        return ok, message

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive() and self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
            self.thread.join(timeout=1.0)
        self.thread = None
        self.thread_id = None
        self._registered = False

    def hotkey_listener_loop(self, modifiers, vk_code, result_queue):
        self.thread_id = kernel32.GetCurrentThreadId()
        ok = bool(user32.RegisterHotKey(None, HOTKEY_ID, modifiers, vk_code))
        self._registered = ok
        if not ok:
            err_code = ctypes.get_last_error()
            result_queue.put((False, f"快捷键被占用或注册失败（错误 {err_code}）"))
            return

        result_queue.put((True, "快捷键注册成功"))
        msg = wintypes.MSG()
        try:
            while not self.stop_event.is_set():
                ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if ret == 0 or msg.message == WM_QUIT:
                    break
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID and self.callback:
                    self.callback(list(self.release_keys))
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)
            self._registered = False

    def _parse_main_key(self, token):
        if len(token) == 1 and token.isalpha():
            return ord(token.upper())
        if len(token) == 1 and token.isdigit():
            return ord(token)
        if token.startswith("f") and token[1:].isdigit():
            number = int(token[1:])
            if 1 <= number <= 24:
                return 0x70 + number - 1
        if token in self.VK_NAMES:
            return self.VK_NAMES[token]
        raise ValueError(f"不支持的主键：{token}")

    def _modifier_release_keys(self, modifier):
        if modifier == MOD_CONTROL:
            return [Key.ctrl, Key.ctrl_l, Key.ctrl_r]
        if modifier == MOD_ALT:
            return [Key.alt, Key.alt_l, Key.alt_r]
        if modifier == MOD_SHIFT:
            return [Key.shift, Key.shift_l, Key.shift_r]
        if modifier == MOD_WIN:
            return [Key.cmd, Key.cmd_l, Key.cmd_r]
        return []

    def _main_release_keys(self, token):
        special = {
            "enter": Key.enter,
            "tab": Key.tab,
            "space": Key.space,
            "esc": Key.esc,
            "escape": Key.esc,
            "home": Key.home,
            "end": Key.end,
            "pageup": Key.page_up,
            "pagedown": Key.page_down,
            "delete": Key.delete,
            "del": Key.delete,
            "backspace": Key.backspace,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
        }
        if token in special:
            return [special[token]]
        if len(token) == 1:
            return [token.lower()]
        if token.startswith("f") and token[1:].isdigit():
            number = int(token[1:])
            if 1 <= number <= 24:
                return [getattr(Key, f"f{number}")]
        return []
