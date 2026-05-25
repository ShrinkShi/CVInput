import json
import sys
from pathlib import Path


SUPPORTED_LANGUAGES = ("zh_cn", "en_us")
DEFAULT_LANGUAGE = "zh_cn"

BUILTIN_FALLBACK = {
    "app.title": "CVInput",
    "app.subtitle": "模拟键盘输入粘贴工具",
    "tooltip.settings": "设置",
    "tooltip.about": "关于",
    "tooltip.pin": "窗口置顶",
    "tooltip.minimize": "最小化",
    "tooltip.close": "关闭",
    "tooltip.type": "输入",
    "tooltip.stop": "停止",
    "tooltip.read_clipboard": "读取剪贴板",
    "tooltip.apply_hotkey": "应用快捷键",
    "tooltip.apply_interval": "应用输入间隔",
    "tooltip.github": "GitHub",
    "tooltip.email": "Email",
    "label.listen": "监听",
    "label.settings": "设置",
    "label.about": "关于",
    "label.hotkey": "快捷键",
    "label.interval": "输入间隔",
    "label.opacity": "透明度",
    "label.auto_clipboard": "自动监听剪贴板",
    "label.clear_after_typing": "输入后清空",
    "label.disable_hotkey_when_clipboard_empty": "剪贴板无文本时不接管快捷键",
    "label.toggle_ime_with_shift": "输入前后切换英文输入状态",
    "label.newline_with_shift_enter": "换行使用 Shift+Enter",
    "label.multi_slot_enabled": "多条复制内容手动输入",
    "label.multi_slots": "多槽位输入",
    "label.slot_1": "Alt+1",
    "label.slot_2": "Alt+2",
    "label.slot_3": "Alt+3",
    "label.slot_4": "Alt+4",
    "label.slot_5": "Alt+5",
    "label.slot_6": "Alt+6",
    "label.slot_7": "Alt+7",
    "label.slot_8": "Alt+8",
    "label.slot_9": "Alt+9",
    "label.slot_0": "Alt+0",
    "label.close_to_tray": "关闭时最小化到托盘",
    "label.startup_on_boot": "开机自启",
    "label.language": "语言",
    "label.apply": "应用",
    "label.restore_defaults": "恢复默认设置",
    "label.author": "作者",
    "label.project": "剪贴板转模拟输入工具",
    "label.github": "GitHub",
    "label.email": "Email",
    "label.language.zh_cn": "中文",
    "label.language.en_us": "English",
    "status.starting": "启动中",
    "status.listening_hotkey": "监听中 · {hotkey}",
    "status.hotkey_failed": "快捷键注册失败，请更换",
    "status.hotkey_empty": "快捷键不能为空",
    "status.hotkey_applied": "快捷键已应用 · {hotkey}",
    "status.hotkey_released_empty": "剪贴板无文本，{hotkey} 已释放",
    "status.hotkey_registered": "快捷键已注册：{hotkey}",
    "status.interval_updated": "输入间隔已更新：{interval}s",
    "status.interval_invalid": "输入间隔需在 0.005 到 1.0 秒之间",
    "status.defaults_restored": "已恢复默认设置",
    "status.slot_hotkey_failed": "槽位快捷键注册失败：{slots}",
    "status.slot_empty": "{slot} 槽位为空",
    "status.text_empty": "文本为空",
    "status.typing": "正在输入",
    "status.stopped": "已停止",
    "status.done": "输入完成",
    "status.typing_failed": "输入失败：{error}",
    "status.stopping": "正在停止输入",
    "status.clipboard_chars": "剪贴板 {count} 字符",
    "status.clipboard_failed": "剪贴板读取失败：{error}",
    "status.clipboard_on": "剪贴板监听已开启",
    "status.clipboard_off": "剪贴板监听已关闭",
    "status.topmost_on": "窗口置顶已开启",
    "status.topmost_off": "窗口置顶已关闭",
    "status.close_to_tray_on": "关闭时将最小化到托盘",
    "status.close_to_tray_off": "关闭时将退出程序",
    "status.startup_on": "开机自启已开启",
    "status.startup_off": "开机自启已关闭",
    "status.startup_failed": "开机自启设置失败：{error}",
    "status.language_changed": "语言已切换",
    "status.email_copied": "邮箱已复制",
    "status.email_copy_failed": "邮箱复制失败：{error}",
    "status.window_hidden": "已最小化到托盘",
    "tray.show_hide": "显示/隐藏窗口",
    "tray.exit": "退出",
    "about.author": "Shrink",
    "about.description": "剪贴板转模拟输入工具",
    "about.idea": "Clipboard → Simulated Typing",
    "about.watermark": "时锐牛逼",
}


class Translator:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        self.default_messages = self._load_language(DEFAULT_LANGUAGE)
        self.messages = self._load_language(self.language)

    def set_language(self, language):
        self.language = language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
        self.messages = self._load_language(self.language)

    def t(self, key, **kwargs):
        value = self.messages.get(key) or self.default_messages.get(key) or BUILTIN_FALLBACK.get(key) or key
        if kwargs:
            try:
                return value.format(**kwargs)
            except Exception:
                return value
        return value

    def _load_language(self, language):
        messages = dict(BUILTIN_FALLBACK if language == DEFAULT_LANGUAGE else {})
        path = self._locale_path(language)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return messages
        if isinstance(data, dict):
            messages.update({str(key): str(value) for key, value in data.items()})
        return messages

    def _locale_path(self, language):
        if getattr(sys, "frozen", False):
            base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
            packed = base / "cvinput" / "locales" / f"{language}.json"
            if packed.exists():
                return packed
        return Path(__file__).resolve().parent / "locales" / f"{language}.json"
