import ctypes
import os
from ctypes import wintypes


INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001
VK_LSHIFT = 0xA0
VK_RETURN = 0x0D
SCAN_LSHIFT = 0x2A
SCAN_RETURN = 0x1C

_IS_WINDOWS = os.name == "nt"

if _IS_WINDOWS:
    ULONG_PTR = wintypes.WPARAM

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class _INPUT_UNION(ctypes.Union):
        # SendInput validates cbSize against the full Win32 INPUT union.
        # The mouse member is larger than KEYBDINPUT on 64-bit Windows.
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]

    _user32 = ctypes.WinDLL("user32", use_last_error=True)
    _send_input = _user32.SendInput
    _send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    _send_input.restype = wintypes.UINT


class SendInputError(OSError):
    def __init__(self, sent, last_error, expected):
        self.sent = sent
        self.last_error = last_error
        self.expected = expected
        super().__init__(last_error, f"SendInput sent {sent}/{expected}")


def _keyboard_input(virtual_key=0, scan_code=0, flags=0):
    event = INPUT()
    event.type = INPUT_KEYBOARD
    event.ki.wVk = virtual_key
    event.ki.wScan = scan_code
    event.ki.dwFlags = flags
    return event


def _send_inputs(events):
    expected = len(events)
    ctypes.set_last_error(0)
    event_array = (INPUT * expected)(*events)
    sent = _send_input(expected, event_array, ctypes.sizeof(INPUT))
    last_error = ctypes.get_last_error()
    if sent != expected:
        raise SendInputError(sent, last_error, expected)
    return sent, last_error


def is_available():
    return _IS_WINDOWS


def is_64_bit_process():
    return _IS_WINDOWS and ctypes.sizeof(ctypes.c_void_p) == 8


def is_64_bit_windows():
    if not _IS_WINDOWS:
        return False
    return (
        ctypes.sizeof(ctypes.c_void_p) == 8
        or bool(os.environ.get("PROCESSOR_ARCHITEW6432"))
        or "PROGRAMFILES(X86)" in os.environ
    )


def send_key_event(virtual_key, key_up=False):
    if not _IS_WINDOWS:
        raise OSError("Win32 SendInput is only available on Windows")

    flags = KEYEVENTF_KEYUP if key_up else 0
    return _send_inputs([_keyboard_input(virtual_key=virtual_key, flags=flags)])


def send_key_chord(modifier_key, main_key):
    if not _IS_WINDOWS:
        raise OSError("Win32 SendInput is only available on Windows")

    return _send_inputs(
        [
            _keyboard_input(virtual_key=modifier_key),
            _keyboard_input(virtual_key=main_key),
            _keyboard_input(virtual_key=main_key, flags=KEYEVENTF_KEYUP),
            _keyboard_input(virtual_key=modifier_key, flags=KEYEVENTF_KEYUP),
        ]
    )


def send_scan_event(scan_code, key_up=False, extended=False):
    if not _IS_WINDOWS:
        raise OSError("Win32 SendInput is only available on Windows")

    flags = KEYEVENTF_SCANCODE
    if key_up:
        flags |= KEYEVENTF_KEYUP
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY

    return _send_inputs([_keyboard_input(scan_code=scan_code, flags=flags)])


def send_scan_chord(modifier_scan_code, main_scan_code):
    if not _IS_WINDOWS:
        raise OSError("Win32 SendInput is only available on Windows")

    return _send_inputs(
        [
            _keyboard_input(scan_code=modifier_scan_code, flags=KEYEVENTF_SCANCODE),
            _keyboard_input(scan_code=main_scan_code, flags=KEYEVENTF_SCANCODE),
            _keyboard_input(scan_code=main_scan_code, flags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP),
            _keyboard_input(scan_code=modifier_scan_code, flags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP),
        ]
    )


def send_unicode_text(text):
    if not _IS_WINDOWS:
        raise OSError("Win32 SendInput is only available on Windows")

    encoded = str(text).encode("utf-16-le")
    events = []
    for index in range(0, len(encoded), 2):
        unit = int.from_bytes(encoded[index : index + 2], "little")
        events.append(_keyboard_input(scan_code=unit, flags=KEYEVENTF_UNICODE))
        events.append(_keyboard_input(scan_code=unit, flags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
    if not events:
        return 0, 0
    return _send_inputs(events)
