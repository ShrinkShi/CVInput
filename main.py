import ctypes
import queue
import threading
import time
import tkinter as tk
from ctypes import wintypes
from tkinter import messagebox, ttk

import pyperclip
from pynput.keyboard import Controller, Key


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
HOTKEY_ID = 1

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


class ClipboardMonitor:
    def __init__(self, on_text, should_skip):
        self.on_text = on_text
        self.should_skip = should_skip
        self.stop_event = threading.Event()
        self.thread = None
        self.last_text = None
        self.enabled = True

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.thread = None

    def set_enabled(self, enabled):
        self.enabled = enabled

    def monitor_loop(self):
        while not self.stop_event.is_set():
            if self.enabled:
                try:
                    text = pyperclip.paste()
                    if isinstance(text, str) and text != self.last_text:
                        self.last_text = text
                        if not self.should_skip():
                            self.on_text(text)
                except Exception as e:
                    err_msg = str(e)
                    self.on_text(None, err_msg)
            time.sleep(0.5)


class TypingEngine:
    def __init__(self):
        self.controller = Controller()

    def type_text(self, text, interval, stop_event, release_keys):
        self._release_trigger_keys(release_keys)
        time.sleep(0.05)
        for char in text:
            if stop_event.is_set():
                break
            if char == "\n":
                self.controller.press(Key.enter)
                self.controller.release(Key.enter)
            elif char == "\t":
                self.controller.press(Key.tab)
                self.controller.release(Key.tab)
            else:
                self.controller.type(char)
            time.sleep(interval)

    def _release_trigger_keys(self, release_keys):
        for key in release_keys:
            try:
                self.controller.release(key)
            except Exception:
                pass


class CVInputApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CVInput")
        self.root.geometry("320x180+980+120")
        self.root.minsize(260, 90)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.hotkey_text = tk.StringVar(value="Ctrl+V")
        self.interval = tk.DoubleVar(value=0.03)
        self.always_on_top = tk.BooleanVar(value=True)
        self.listen_clipboard = tk.BooleanVar(value=True)
        self.clear_after_typing = tk.BooleanVar(value=False)
        self.opacity = tk.DoubleVar(value=1.0)
        self.status_text = tk.StringVar(value="启动中")
        self.short_status = tk.StringVar(value="监听中")
        self.mini_mode = False

        self.hotkey_manager = HotkeyManager()
        self.clipboard_monitor = ClipboardMonitor(self.schedule_clipboard_update, self.is_text_focused)
        self.typing_engine = TypingEngine()
        self.typing_stop_event = threading.Event()
        self.typing_thread = None
        self.last_release_keys = []

        self.create_ui()
        self.clipboard_monitor.start()
        self.register_hotkey()

    def create_ui(self):
        self.root.configure(bg="#f5f6f8")
        self.main_frame = ttk.Frame(self.root, padding=(8, 6, 8, 4))
        self.main_frame.pack(fill="both", expand=True)

        top = ttk.Frame(self.main_frame)
        top.pack(fill="x")
        ttk.Label(top, text="CVInput", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.status_badge = ttk.Label(top, textvariable=self.short_status, font=("Segoe UI", 8))
        self.status_badge.pack(side="left", padx=(8, 0))
        ttk.Button(top, text="⚙", width=3, command=self.open_settings).pack(side="right")
        ttk.Button(top, text="—", width=3, command=self.toggle_mini_mode).pack(side="right", padx=(0, 4))

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, pady=(6, 4))

        text_wrap = ttk.Frame(self.content_frame)
        text_wrap.pack(fill="both", expand=True)
        self.text_box = tk.Text(
            text_wrap,
            height=4,
            wrap="word",
            font=("Segoe UI", 9),
            undo=True,
            relief="solid",
            borderwidth=1,
        )
        scrollbar = ttk.Scrollbar(text_wrap, orient="vertical", command=self.text_box.yview)
        self.text_box.configure(yscrollcommand=scrollbar.set)
        self.text_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.button_row = ttk.Frame(self.content_frame)
        self.button_row.pack(fill="x", pady=(5, 0))
        ttk.Button(self.button_row, text="输入", width=6, command=self.start_typing_from_button).pack(side="left")
        ttk.Button(self.button_row, text="停止", width=6, command=self.stop_typing).pack(side="left", padx=(5, 0))
        ttk.Button(self.button_row, text="读取", width=6, command=self.read_clipboard_now).pack(side="left", padx=(5, 0))
        ttk.Checkbutton(
            self.button_row,
            text="监听",
            variable=self.listen_clipboard,
            command=self.on_clipboard_toggle,
        ).pack(side="right")

        ttk.Label(self.main_frame, textvariable=self.status_text, font=("Segoe UI", 8)).pack(fill="x")

    def register_hotkey(self):
        ok, message = self.hotkey_manager.start(self.hotkey_text.get(), self.on_hotkey)
        if ok:
            self.short_status.set("监听中")
            self.status_text.set(f"快捷键 {self.hotkey_text.get()}")
        else:
            self.short_status.set("快捷键失败")
            self.status_text.set("快捷键注册失败，请更换")
            return message
        return None

    def on_hotkey(self, release_keys):
        self.last_release_keys = release_keys
        self.root.after(0, self.start_typing_from_hotkey)

    def start_typing_from_hotkey(self):
        self.start_typing(self.last_release_keys)

    def start_typing_from_button(self):
        release_keys = []
        self.start_typing(release_keys)

    def start_typing(self, release_keys):
        if self.typing_thread and self.typing_thread.is_alive():
            return
        text = self.text_box.get("1.0", "end-1c")
        if not text:
            self.status_text.set("文本为空")
            return
        self.typing_stop_event.clear()
        self.short_status.set("输入中")
        self.status_text.set("正在输入...")
        self.typing_thread = threading.Thread(
            target=self._typing_worker,
            args=(text, float(self.interval.get()), release_keys),
            daemon=True,
        )
        self.typing_thread.start()

    def _typing_worker(self, text, interval, release_keys):
        try:
            self.typing_engine.type_text(text, interval, self.typing_stop_event, release_keys)
            stopped = self.typing_stop_event.is_set()
            self.root.after(0, lambda: self.on_typing_done(stopped))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: self.on_typing_error(msg))

    def on_typing_done(self, stopped):
        self.short_status.set("监听中")
        self.status_text.set("已停止" if stopped else "输入完成")
        if not stopped and self.clear_after_typing.get():
            self.text_box.delete("1.0", "end")

    def on_typing_error(self, message):
        self.short_status.set("已停止")
        self.status_text.set(f"输入失败：{message}")

    def stop_typing(self):
        self.typing_stop_event.set()
        self.status_text.set("正在停止输入...")

    def schedule_clipboard_update(self, text, error=None):
        if error:
            self.root.after(0, lambda msg=error: self.status_text.set(f"剪贴板读取失败：{msg}"))
            return
        self.root.after(0, lambda value=text: self.update_text_from_clipboard(value))

    def update_text_from_clipboard(self, text):
        if self.is_text_focused():
            return
        self.text_box.delete("1.0", "end")
        self.text_box.insert("1.0", text)
        self.status_text.set(f"剪贴板 {len(text)} 字符")

    def read_clipboard_now(self):
        try:
            text = pyperclip.paste()
        except Exception as e:
            err_msg = str(e)
            self.status_text.set(f"剪贴板读取失败：{err_msg}")
            return
        self.update_text_from_clipboard(text if isinstance(text, str) else "")

    def is_text_focused(self):
        return self.root.focus_get() is self.text_box

    def on_clipboard_toggle(self):
        self.clipboard_monitor.set_enabled(self.listen_clipboard.get())
        self.status_text.set("剪贴板监听已开启" if self.listen_clipboard.get() else "剪贴板监听已关闭")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("300x260")
        win.transient(self.root)
        win.resizable(False, False)
        win.attributes("-topmost", self.always_on_top.get())

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="快捷键").grid(row=0, column=0, sticky="w")
        hotkey_entry = ttk.Entry(frame, textvariable=self.hotkey_text, width=18)
        hotkey_entry.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(frame, text="输入间隔").grid(row=1, column=0, sticky="w")
        interval_spin = ttk.Spinbox(frame, from_=0.005, to=0.5, increment=0.005, textvariable=self.interval, width=16)
        interval_spin.grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Label(frame, text="透明度").grid(row=2, column=0, sticky="w")
        opacity_scale = ttk.Scale(frame, from_=0.55, to=1.0, variable=self.opacity, command=self.on_opacity_change)
        opacity_scale.grid(row=2, column=1, sticky="ew", pady=3)

        ttk.Checkbutton(frame, text="窗口置顶", variable=self.always_on_top, command=self.on_topmost_change).grid(row=3, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(frame, text="启动时自动监听剪贴板", variable=self.listen_clipboard, command=self.on_clipboard_toggle).grid(row=4, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(frame, text="输入后清空文本框", variable=self.clear_after_typing).grid(row=5, column=0, columnspan=2, sticky="w", pady=3)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(button_frame, text="应用快捷键", command=lambda: self.apply_hotkey(win)).pack(side="left")
        ttk.Button(button_frame, text="迷你/展开", command=self.toggle_mini_mode).pack(side="left", padx=(6, 0))
        ttk.Button(button_frame, text="关于", command=self.show_about).pack(side="right")

        frame.columnconfigure(1, weight=1)

    def apply_hotkey(self, parent):
        message = self.register_hotkey()
        if message:
            messagebox.showwarning("快捷键注册失败", "快捷键被占用或注册失败，请更换。", parent=parent)

    def on_topmost_change(self):
        enabled = self.always_on_top.get()
        self.root.attributes("-topmost", enabled)
        self.status_text.set("窗口置顶已开启" if enabled else "窗口置顶已关闭")

    def on_opacity_change(self, _value=None):
        self.root.attributes("-alpha", self.opacity.get())

    def toggle_mini_mode(self):
        self.mini_mode = not self.mini_mode
        if self.mini_mode:
            self.content_frame.pack_forget()
            self.root.geometry("260x72")
            self.status_text.set("迷你模式")
        else:
            self.content_frame.pack(fill="both", expand=True, pady=(6, 4))
            self.root.geometry("320x180")
            self.status_text.set("展开模式")

    def show_about(self):
        messagebox.showinfo("关于 CVInput", "CVInput 0.1\n剪贴板转模拟输入小工具", parent=self.root)

    def on_close(self):
        self.typing_stop_event.set()
        self.clipboard_monitor.stop()
        self.hotkey_manager.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CVInputApp()
    app.run()
