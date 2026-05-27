from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock


MAX_LOG_LINES = 5000

_enabled = False
_lines = deque(maxlen=MAX_LOG_LINES)
_lock = Lock()


def set_debug_enabled(enabled):
    global _enabled
    _enabled = bool(enabled)


def is_debug_enabled():
    return _enabled


def debug_log(category, message, **data):
    if not _enabled:
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
    with _lock:
        if not _lines:
            return str(empty_text)
        return "\n".join(_lines) + "\n"


def _format_value(value):
    try:
        return repr(value)
    except Exception:
        return "<unrepresentable>"
