import json
import os
import copy
from pathlib import Path

from .constants import (
    DEFAULT_INTERVAL_MS,
    DEFAULT_SINGLE_LINE_REPLACEMENT,
    DEFAULT_TYPING_INTERVAL_MODE,
    DEFAULT_TYPING_TARGET_DURATION_MS,
    DEFAULT_TYPING_MODE,
    DEFAULT_INPUT_ENCODING,
    DEFAULT_OUTPUT_ENCODING,
    INPUT_ENCODINGS,
    NEWLINE_METHOD_VERSION,
    NEWLINE_METHODS,
    NEWLINE_METHOD_PYAUTOGUI,
    NEWLINE_METHOD_WIN32_SCAN,
    NEWLINE_METHOD_WIN32_VK,
    OUTPUT_ENCODINGS,
    SINGLE_LINE_REPLACEMENTS,
    TYPING_INTERVAL_MODE_CUSTOM_INTERVAL,
    TYPING_INTERVAL_MODE_DEFAULT,
    TYPING_INTERVAL_MODES,
    TYPING_MODES,
    DEFAULT_CONFIG,
)


class ConfigStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else self.default_path()

    def default_path(self):
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "CVInput" / "config.json"
        return Path.home() / ".cvinput" / "config.json"

    def load(self):
        config = copy.deepcopy(DEFAULT_CONFIG)
        if not self.path.exists():
            return config
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return config
        if isinstance(data, dict):
            if data.get("remember_settings") is False:
                config["remember_settings"] = False
                return config
            if "interval_ms" not in data and "interval" in data:
                try:
                    data["interval_ms"] = float(data["interval"]) * 1000
                    data.setdefault("custom_interval_enabled", True)
                except (TypeError, ValueError):
                    pass
            if "typing_interval_ms" not in data:
                for key in ("interval_ms", "typing_interval", "input_interval"):
                    if key in data:
                        try:
                            data["typing_interval_ms"] = float(data[key])
                        except (TypeError, ValueError):
                            pass
                        break
            if "interval_ms" not in data and "typing_interval_ms" in data:
                data["interval_ms"] = data["typing_interval_ms"]
            if "typing_interval_mode" not in data:
                legacy_custom = data.get("custom_typing_interval", data.get("custom_interval_enabled"))
                data["typing_interval_mode"] = (
                    TYPING_INTERVAL_MODE_CUSTOM_INTERVAL
                    if bool(legacy_custom)
                    else TYPING_INTERVAL_MODE_DEFAULT
                )
            if "input_hotkey" not in data and "hotkey" in data:
                data["input_hotkey"] = data["hotkey"]
            if "input_mode" not in data and "typing_mode" in data:
                data["input_mode"] = data["typing_mode"]
            if "typing_mode" not in data and "input_mode" in data:
                data["typing_mode"] = data["input_mode"]
            if "developer_mode" not in data and "debug_mode" in data:
                data["developer_mode"] = bool(data.get("debug_mode"))
                if data["developer_mode"] and "debug_window_position" not in data:
                    data["debug_window_position"] = True
            if data.get("newline_shift_enter_method_version") != NEWLINE_METHOD_VERSION:
                legacy_method = data.get("newline_shift_enter_method")
                if legacy_method == "auto":
                    data["newline_shift_enter_method"] = NEWLINE_METHOD_PYAUTOGUI
                elif legacy_method == "win64":
                    data["newline_shift_enter_method"] = NEWLINE_METHOD_WIN32_SCAN
                elif legacy_method == "win32":
                    data["newline_shift_enter_method"] = NEWLINE_METHOD_WIN32_VK
                elif legacy_method not in NEWLINE_METHODS:
                    data["newline_shift_enter_method"] = DEFAULT_CONFIG["newline_shift_enter_method"]
                data["newline_shift_enter_method_version"] = NEWLINE_METHOD_VERSION
            config.update({key: data[key] for key in config.keys() & data.keys()})
        if config.get("newline_shift_enter_method") not in NEWLINE_METHODS:
            config["newline_shift_enter_method"] = DEFAULT_CONFIG["newline_shift_enter_method"]
        config["newline_shift_enter_method_version"] = NEWLINE_METHOD_VERSION
        mode = config.get("input_mode", config.get("typing_mode", DEFAULT_TYPING_MODE))
        if mode not in TYPING_MODES:
            mode = DEFAULT_TYPING_MODE
        config["input_mode"] = mode
        config["typing_mode"] = mode
        if config.get("single_line_replacement") not in SINGLE_LINE_REPLACEMENTS:
            config["single_line_replacement"] = DEFAULT_SINGLE_LINE_REPLACEMENT
        interval_mode = config.get("typing_interval_mode", DEFAULT_TYPING_INTERVAL_MODE)
        if interval_mode not in TYPING_INTERVAL_MODES:
            interval_mode = DEFAULT_TYPING_INTERVAL_MODE
        config["typing_interval_mode"] = interval_mode
        config["custom_interval_enabled"] = interval_mode == TYPING_INTERVAL_MODE_CUSTOM_INTERVAL
        try:
            interval_ms = float(config.get("typing_interval_ms", config.get("interval_ms", DEFAULT_INTERVAL_MS)))
        except (TypeError, ValueError):
            interval_ms = DEFAULT_INTERVAL_MS
        config["typing_interval_ms"] = interval_ms
        config["interval_ms"] = interval_ms
        try:
            target_duration_ms = float(config.get("typing_target_duration_ms", DEFAULT_TYPING_TARGET_DURATION_MS))
        except (TypeError, ValueError):
            target_duration_ms = DEFAULT_TYPING_TARGET_DURATION_MS
        if not 1 <= target_duration_ms <= 10000:
            target_duration_ms = DEFAULT_TYPING_TARGET_DURATION_MS
        config["typing_target_duration_ms"] = target_duration_ms
        if config.get("input_encoding") not in INPUT_ENCODINGS:
            config["input_encoding"] = DEFAULT_INPUT_ENCODING
        if config.get("output_encoding") not in OUTPUT_ENCODINGS:
            config["output_encoding"] = DEFAULT_OUTPUT_ENCODING
        return config

    def save(self, config):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not config.get("remember_settings", True):
            self.path.write_text(json.dumps({"remember_settings": False}, ensure_ascii=False, indent=2), encoding="utf-8")
            return
        data = copy.deepcopy(DEFAULT_CONFIG)
        data.update({key: config[key] for key in data.keys() & config.keys()})
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
