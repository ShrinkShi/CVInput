import ctypes
import sys


def enable_dpi_awareness():
    if not sys.platform.startswith("win"):
        return

    if _set_process_dpi_awareness_context():
        return
    if _set_process_dpi_awareness():
        return
    _set_process_dpi_aware()


def _set_process_dpi_awareness_context():
    try:
        user32 = ctypes.windll.user32
        set_context = getattr(user32, "SetProcessDpiAwarenessContext", None)
        if set_context is None:
            return False
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_bool
        return bool(set_context(ctypes.c_void_p(-4)))  # PER_MONITOR_AWARE_V2
    except Exception:
        return False


def set_app_user_model_id(app_id="CVInput.CVInput"):
    if not sys.platform.startswith("win"):
        return False
    try:
        shell32 = ctypes.windll.shell32
        set_app_id = getattr(shell32, "SetCurrentProcessExplicitAppUserModelID", None)
        if set_app_id is None:
            return False
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        return set_app_id(app_id) == 0
    except Exception:
        return False


def _set_process_dpi_awareness():
    try:
        shcore = ctypes.windll.shcore
        set_awareness = getattr(shcore, "SetProcessDpiAwareness", None)
        if set_awareness is None:
            return False
        set_awareness.argtypes = [ctypes.c_int]
        set_awareness.restype = ctypes.c_long
        return set_awareness(2) == 0  # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        return False


def _set_process_dpi_aware():
    try:
        user32 = ctypes.windll.user32
        set_aware = getattr(user32, "SetProcessDPIAware", None)
        if set_aware is None:
            return False
        set_aware.restype = ctypes.c_bool
        return bool(set_aware())
    except Exception:
        return False
