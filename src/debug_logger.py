from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock


MAX_LOG_LINES = 5000
CATEGORY_WINDOW_POSITION = "WINDOW_POSITION"
CATEGORY_NEWLINE_BEHAVIOR = "NEWLINE_BEHAVIOR"

_developer_mode = False
_category_enabled = {
    CATEGORY_WINDOW_POSITION: False,
    CATEGORY_NEWLINE_BEHAVIOR: False,
}
_lines = deque(maxlen=MAX_LOG_LINES)
_lock = Lock()


def set_developer_mode(enabled):
    global _developer_mode
    _developer_mode = bool(enabled)


def is_developer_mode():
    return _developer_mode


def set_category_enabled(category, enabled):
    _category_enabled[_normalize_category(category)] = bool(enabled)


def is_category_enabled(category):
    return bool(_category_enabled.get(_normalize_category(category), False))


def configure_debug(developer_mode=False, categories=None):
    set_developer_mode(developer_mode)
    for category, enabled in (categories or {}).items():
        set_category_enabled(category, enabled)


def set_debug_enabled(enabled):
    set_developer_mode(enabled)


def is_debug_enabled():
    return is_developer_mode()


def debug_log(category, message, **data):
    category = _normalize_category(category)
    if not _developer_mode or not is_category_enabled(category):
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    details = " ".join(f"{key}={_format_value(value)}" for key, value in data.items())
    line = f"[{timestamp}] [{str(category).upper()}] {message}"
    if details:
        line = f"{line} {details}"
    with _lock:
        _lines.append(line)
    print(line, flush=True)


def export_debug_log(path, empty_text="No debug logs yet"):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(get_debug_log_text(empty_text=empty_text), encoding="utf-8")


def clear_debug_log():
    with _lock:
        _lines.clear()


def get_debug_log_text(empty_text="No debug logs yet"):
    header = _debug_state_text()
    with _lock:
        if not _lines:
            return f"{header}\n{str(empty_text)}\n"
        return f"{header}\n" + "\n".join(_lines) + "\n"


def get_debug_log_count():
    with _lock:
        return len(_lines)


def _debug_state_text():
    categories = ", ".join(f"{key}={value}" for key, value in sorted(_category_enabled.items()))
    return f"Developer mode: {_developer_mode}\nCategories: {categories}"


def _format_value(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepresentable>"


def _normalize_category(category):
    normalized = str(category).upper()
    aliases = {
        "DPI": CATEGORY_WINDOW_POSITION,
        "POPUP": CATEGORY_WINDOW_POSITION,
        "WINDOW": CATEGORY_WINDOW_POSITION,
    }
    return aliases.get(normalized, normalized)
