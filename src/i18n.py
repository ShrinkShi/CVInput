import json
import sys
from pathlib import Path


SUPPORTED_LANGUAGES = ("zh_cn", "en_us")
DEFAULT_LANGUAGE = "zh_cn"

BUILTIN_FALLBACK = {
    "app.title": "CVI",
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
    "tooltip.listen_switch": "开启后自动同步剪贴板文本。",
    "tooltip.hotkeys_switch": "开启后输入快捷键和多槽位快捷键生效；关闭后只能使用按钮操作。",
    "tooltip.setting.custom_interval_enabled": "默认关闭，开启后显示可调节输入间隔。",
    "tooltip.setting.auto_clipboard": "开启后自动读取最新剪贴板文本并显示在主文本框中。",
    "tooltip.setting.clear_after_typing": "开启后，每次模拟输入完成后清空主文本框。",
    "tooltip.setting.disable_hotkey_when_clipboard_empty": "开启后，剪贴板无文本时释放输入快捷键，避免影响系统原生粘贴。",
    "tooltip.setting.toggle_ime_with_shift": "用于缓解中文输入法下中英混合输入异常。",
    "tooltip.setting.newline_with_shift_enter": "开启后，文本换行会模拟 Shift+Enter，适合 Enter 会发送消息的输入框。",
    "tooltip.setting.multi_slot_enabled": "开启后显示 10 个槽位，可用 Alt+1 到 Alt+0 输入对应内容。",
    "tooltip.setting.close_to_tray": "开启后关闭窗口不会退出程序，而是隐藏到系统托盘。",
    "tooltip.setting.startup_on_boot": "开启后随 Windows 登录自动启动。",
    "tooltip.setting.remember_settings": "开启后保存本次设置，下次启动自动恢复。",
    "tooltip.setting.close_popup_on_blur": "开启后点击子窗口外部区域会自动关闭子窗口。",
    "tooltip.setting.debug_mode": "开启后记录窗口定位、DPI、热键、输入等调试信息，便于开发排查问题。",
    "tooltip.export_debug_log": "将当前调试日志导出为文本文件。",
    "label.listen": "监听",
    "label.hotkeys": "热键",
    "label.settings": "设置",
    "label.about": "关于",
    "label.about_with_product": "关于  CVInput",
    "label.hotkey": "快捷键",
    "label.input_hotkey": "输入快捷键",
    "label.hotkey_toggle_hotkey": "热键开关快捷键",
    "label.interval": "输入间隔(ms)",
    "label.custom_interval_enabled": "自定义输入间隔",
    "label.reset_default_interval": "恢复默认输入间隔",
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
    "label.remember_settings": "下次启动时记住设置项",
    "label.close_popup_on_blur": "子窗口点击空白处关闭",
    "label.debug_mode": "调试模式",
    "label.export_debug_log": "导出调试日志",
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
    "status.input_hotkey_failed": "输入快捷键注册失败",
    "status.hotkey_toggle_failed": "热键开关快捷键注册失败",
    "status.hotkey_empty": "快捷键不能为空",
    "status.hotkey_applied": "快捷键已应用 · {hotkey}",
    "status.hotkey_toggle_applied": "热键开关快捷键已应用 · {hotkey}",
    "status.hotkeys_enabled": "热键已启用",
    "status.hotkeys_disabled": "热键已禁用",
    "status.hotkey_released_empty": "剪贴板无文本，{hotkey} 已释放",
    "status.hotkey_registered": "快捷键已注册：{hotkey}",
    "status.interval_updated": "输入间隔已更新：{interval}ms",
    "status.interval_invalid": "输入间隔需在 0.1 到 10000 ms 之间",
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
    "status.debug_mode_on": "调试模式已开启",
    "status.debug_mode_off": "调试模式已关闭",
    "status.debug_log_exported": "调试日志已导出",
    "status.debug_log_export_failed": "调试日志导出失败：{error}",
    "status.debug_log_empty": "暂无调试日志",
    "tray.show_hide": "显示/隐藏窗口",
    "tray.exit": "退出",
    "help.body": "1. 复制文本后，内容会自动显示在主文本框中。\n2. 按输入快捷键，默认 Ctrl+V，即可将文本模拟为键盘输入。\n3. 如果剪贴板为空，CVInput 会释放 Ctrl+V，避免影响系统原生粘贴。\n4. 开启“多条复制内容手动输入”后，可使用 Alt+1 到 Alt+0 输入对应槽位内容。\n5. 如果目标程序以管理员权限运行，CVInput 也需要以管理员权限运行。\n6. 中文输入法下如出现中英混合输入异常，可开启“输入前后切换英文输入状态”。\n7. 可在设置中修改快捷键、输入间隔、托盘、自启和语言等选项。",
    "about.author": "Shrink",
    "about.description": "剪贴板转模拟输入工具",
    "about.usage_title": "使用说明",
    "about.notes_title": "注意事项",
    "about.notes": "启用“换行使用 Shift+Enter”后，文本中的换行将模拟为 Shift+Enter，适合 Enter 会直接发送消息的窗口。",
    "about.long_description": "本工具是一款剪贴板转模拟输入的辅助程序。它能够将你复制的任何文本内容，通过模拟真实键盘敲击的方式，逐字输入到当前光标所在的任何窗口中。\n\n主要用途包括：突破网页输入框的“禁止粘贴”限制（如某些后台系统、在线考试页面、支付金额输入框等）；通过模拟人类打字的速度与节奏（支持自定义延迟与抖动），有效降低被前端脚本或行为风控系统判定为自动化机器的风险；在不支持粘贴的远程桌面、虚拟机、老旧软件界面中实现快捷录入。\n\n无需管理员权限，轻量运行，即开即用。",
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
            packed = base / "src" / "locales" / f"{language}.json"
            if packed.exists():
                return packed
        return Path(__file__).resolve().parent / "locales" / f"{language}.json"
