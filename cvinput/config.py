import json
import os
import copy
from pathlib import Path

from .constants import DEFAULT_CONFIG


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
            config.update({key: data[key] for key in config.keys() & data.keys()})
        return config

    def save(self, config):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not config.get("remember_settings", True):
            self.path.write_text(json.dumps({"remember_settings": False}, ensure_ascii=False, indent=2), encoding="utf-8")
            return
        data = copy.deepcopy(DEFAULT_CONFIG)
        data.update({key: config[key] for key in data.keys() & config.keys()})
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
