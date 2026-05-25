import ctypes
import time
from ctypes import wintypes

IME_CMODE_NATIVE = 0x0001
VK_SHIFT = 0x10
KEYEVENTF_KEYUP = 0x0002

user32 = ctypes.WinDLL("user32", use_last_error=True)
imm32 = ctypes.WinDLL("imm32", use_last_error=True)

user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_size_t]
user32.keybd_event.restype = None

imm32.ImmGetContext.argtypes = [wintypes.HWND]
imm32.ImmGetContext.restype = wintypes.HANDLE
imm32.ImmReleaseContext.argtypes = [wintypes.HWND, wintypes.HANDLE]
imm32.ImmReleaseContext.restype = wintypes.BOOL
imm32.ImmGetConversionStatus.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(wintypes.DWORD),
]
imm32.ImmGetConversionStatus.restype = wintypes.BOOL

def is_chinese_ime_active():
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        himc = imm32.ImmGetContext(hwnd)
        if not himc:
            return False
        conversion = wintypes.DWORD()
        sentence = wintypes.DWORD()
        ok = bool(imm32.ImmGetConversionStatus(himc, ctypes.byref(conversion), ctypes.byref(sentence)))
        imm32.ImmReleaseContext(hwnd, himc)
        return ok and bool(conversion.value & IME_CMODE_NATIVE)
    except Exception:
        return False


def tap_shift():
    try:
        user32.keybd_event(VK_SHIFT, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.08)
        return True
    except Exception:
        return False


def maybe_toggle_ime_before_typing(config):
    if not config.get("toggle_ime_with_shift", True):
        return False
    if not is_chinese_ime_active():
        return False
    return tap_shift()


def restore_ime_after_typing(should_restore):
    if should_restore:
        tap_shift()
