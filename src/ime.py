import os
import time

from .debug_logger import CATEGORY_IME, debug_log


ENGLISH_US_LAYOUT_ID = 0x0409
SWITCH_DELAY_SECONDS = 0.08
WM_INPUTLANGCHANGEREQUEST = 0x0050


def _win32_modules():
    if os.name != "nt":
        raise RuntimeError("Windows IME switching is only available on Windows")
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
    except ImportError as exc:
        raise RuntimeError("pywin32 is not installed") from exc
    return win32api, win32con, win32gui, win32process


def get_foreground_window():
    try:
        _win32api, _win32con, win32gui, _win32process = _win32_modules()
        return win32gui.GetForegroundWindow()
    except Exception as exc:
        debug_log(CATEGORY_IME, "ime_detect_failed", error=str(exc))
        return None


def get_window_title(hwnd):
    try:
        _win32api, _win32con, win32gui, _win32process = _win32_modules()
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def is_valid_window(hwnd):
    try:
        _win32api, _win32con, win32gui, _win32process = _win32_modules()
        return bool(hwnd) and bool(win32gui.IsWindow(hwnd))
    except Exception:
        return False


def get_current_layout_id(hwnd):
    try:
        if not hwnd:
            return None
        win32api, _win32con, _win32gui, win32process = _win32_modules()
        thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
        layout = win32api.GetKeyboardLayout(thread_id)
        return layout & 0xFFFF
    except Exception as exc:
        debug_log(
            CATEGORY_IME,
            "ime_detect_failed",
            hwnd=hwnd,
            window_title=get_window_title(hwnd),
            error=str(exc),
        )
        return None


def get_layout_name(lang_id):
    if lang_id is None:
        return "unknown"
    try:
        return f"0x{int(lang_id):04X}"
    except (TypeError, ValueError):
        return str(lang_id)


def switch_to_language(hwnd, lang_id):
    try:
        if not hwnd:
            return False
        win32api, win32con, _win32gui, _win32process = _win32_modules()
        message = getattr(win32con, "WM_INPUTLANGCHANGEREQUEST", WM_INPUTLANGCHANGEREQUEST)
        result = win32api.SendMessage(hwnd, message, 0, int(lang_id))
        return result == 0
    except Exception as exc:
        debug_log(
            CATEGORY_IME,
            "ime_switch_failed",
            hwnd=hwnd,
            window_title=get_window_title(hwnd),
            target_layout=get_layout_name(lang_id),
            success=False,
            error=str(exc),
        )
        return False


def switch_to_english(hwnd):
    return switch_to_language(hwnd, ENGLISH_US_LAYOUT_ID)


def restore_language(hwnd, lang_id):
    return switch_to_language(hwnd, lang_id)


def maybe_toggle_ime_before_typing(config):
    if not config.get("toggle_ime_with_shift", True):
        return None

    hwnd = get_foreground_window()
    if not hwnd:
        debug_log(CATEGORY_IME, "ime_detect_failed", hwnd=hwnd, success=False, error="no foreground window")
        return None

    title = get_window_title(hwnd)
    previous_layout = get_current_layout_id(hwnd)
    debug_log(
        CATEGORY_IME,
        "ime_detected",
        hwnd=hwnd,
        window_title=title,
        previous_layout=get_layout_name(previous_layout),
        target_layout=get_layout_name(ENGLISH_US_LAYOUT_ID),
        success=previous_layout is not None,
    )
    if previous_layout is None:
        return None

    state = {
        "hwnd": hwnd,
        "window_title": title,
        "previous_layout": previous_layout,
        "switched": False,
    }
    if previous_layout == ENGLISH_US_LAYOUT_ID:
        return state

    request_success = switch_to_english(hwnd)
    state["switched"] = request_success
    if request_success:
        time.sleep(SWITCH_DELAY_SECONDS)
    current_layout = get_current_layout_id(hwnd)
    success = current_layout == ENGLISH_US_LAYOUT_ID
    debug_log(
        CATEGORY_IME,
        "ime_switch_to_english",
        hwnd=hwnd,
        window_title=title,
        previous_layout=get_layout_name(previous_layout),
        target_layout=get_layout_name(ENGLISH_US_LAYOUT_ID),
        current_layout=get_layout_name(current_layout),
        request_success=request_success,
        success=success,
    )
    if success:
        return state

    debug_log(
        CATEGORY_IME,
        "ime_switch_failed",
        hwnd=hwnd,
        window_title=title,
        previous_layout=get_layout_name(previous_layout),
        target_layout=get_layout_name(ENGLISH_US_LAYOUT_ID),
        current_layout=get_layout_name(current_layout),
        success=False,
        error="WM_INPUTLANGCHANGEREQUEST did not switch layout"
        if request_success
        else "WM_INPUTLANGCHANGEREQUEST request failed",
    )
    return state


def restore_ime_after_typing(state):
    if not state:
        return
    if not state.get("switched"):
        return

    hwnd = state.get("hwnd")
    previous_layout = state.get("previous_layout")
    title = state.get("window_title", "")
    if not is_valid_window(hwnd):
        debug_log(
            CATEGORY_IME,
            "ime_restore_failed",
            hwnd=hwnd,
            window_title=title,
            previous_layout=get_layout_name(previous_layout),
            success=False,
            error="target window is no longer valid",
        )
        return

    success = restore_language(hwnd, previous_layout)
    debug_log(
        CATEGORY_IME,
        "ime_restore",
        hwnd=hwnd,
        window_title=title,
        previous_layout=get_layout_name(previous_layout),
        target_layout=get_layout_name(previous_layout),
        success=success,
        error="" if success else "WM_INPUTLANGCHANGEREQUEST did not restore layout",
    )
    if success:
        time.sleep(SWITCH_DELAY_SECONDS)
