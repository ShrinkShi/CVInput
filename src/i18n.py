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
    "tooltip.apply_stop_hotkey": "应用停止输入快捷键",
    "tooltip.apply_interval": "应用输入间隔",
    "tooltip.apply_target_duration": "应用完成时间",
    "tooltip.apply_mode": "应用模式与单行替换字符",
    "tooltip.apply_encoding": "应用输入/输出编码设置",
    "tooltip.github": "GitHub",
    "tooltip.email": "Email",
    "tooltip.listen_switch": "开启后自动同步剪贴板文本。",
    "tooltip.hotkeys_switch": "开启后输入快捷键和多槽位快捷键生效；关闭后只能使用按钮操作。",
    "tooltip.setting.custom_interval_enabled": "默认关闭，开启后显示可调节输入间隔。",
    "tooltip.setting.typing_interval_mode": "默认模式使用项目默认间隔；自定义间隔模式使用固定字符间隔；完成时间模式按文本长度动态计算间隔。",
    "tooltip.setting.auto_clipboard": "开启后自动读取最新剪贴板文本并显示在主文本框中。",
    "tooltip.setting.clear_after_typing": "开启后，每次模拟输入完成后清空主文本框。",
    "tooltip.setting.disable_hotkey_when_clipboard_empty": "开启后，剪贴板无文本时释放输入快捷键，避免影响系统原生粘贴。",
    "tooltip.setting.toggle_ime_with_shift": "用于缓解中文输入法下中英混合输入异常。",
    "tooltip.setting.typing_mode": "默认模式模拟 Shift+Enter；单行模式替换换行；分裂模式每次仅输入一行。",
    "tooltip.setting.single_line_replacement": "选择单行模式中用于替代换行符的字符。",
    "tooltip.setting.input_encoding": "输入文本的解码方式；剪贴板文本通常已是 Unicode，自动检测适合作为默认值。",
    "tooltip.setting.output_encoding": "导出调试日志等文本文件时使用的编码。",
    "tooltip.setting.newline_backend": "开发者实验项：选择默认模式使用的底层 Shift+Enter 模拟实现。",
    "tooltip.mode.default": "模拟 Shift+Enter，适合普通输入框。",
    "tooltip.mode.single_line": "将换行替换为空格或 Tab，适合 AI 输入框等不需要严格换行格式的场景。",
    "tooltip.mode.split": "按行拆分剪贴板内容，每次快捷键只输入一行，适合聊天软件等高风险输入框。",
    "tooltip.setting.multi_slot_enabled": "开启后显示 10 个槽位，可用 Alt+1 到 Alt+0 输入对应内容。",
    "tooltip.setting.close_to_tray": "开启后关闭窗口不会退出程序，而是隐藏到系统托盘。",
    "tooltip.setting.startup_on_boot": "开启后随 Windows 登录自动启动。",
    "tooltip.setting.remember_settings": "开启后保存本次设置，下次启动自动恢复。",
    "tooltip.setting.close_popup_on_blur": "开启后点击子窗口外部区域会自动关闭子窗口。",
    "tooltip.setting.developer_mode": "开启后显示开发者调试窗口，用于控制不同类型的调试日志。",
    "tooltip.setting.debug_window_position": "记录设置、关于等子窗口的尺寸、坐标、DPI 和跟随移动数据。",
    "tooltip.setting.debug_newline_behavior": "记录文本输入过程中遇到换行符时的处理方式，例如普通 Enter、Shift+Enter、按键按下/释放顺序。",
    "tooltip.export_debug_log": "将当前调试日志导出为文本文件。",
    "tooltip.clear_debug_log": "清空当前内存中的调试日志。",
    "label.listen": "监听",
    "label.hotkeys": "热键",
    "label.settings": "设置",
    "label.about": "关于",
    "label.about_with_product": "关于  CVInput",
    "label.hotkey": "快捷键",
    "label.input_hotkey": "输入快捷键",
    "label.stop_typing_hotkey": "停止输入快捷键",
    "label.hotkey_toggle_hotkey": "热键开关快捷键",
    "label.interval": "输入间隔(ms)",
    "label.target_duration": "完成时间(ms)",
    "label.typing_interval_mode": "输入间隔模式",
    "label.typing_interval_mode.default": "默认模式",
    "label.typing_interval_mode.custom_interval": "自定义间隔模式",
    "label.typing_interval_mode.target_duration": "完成时间模式",
    "label.custom_interval_enabled": "自定义输入间隔",
    "label.reset_default_interval": "恢复默认输入间隔",
    "label.opacity": "透明度",
    "label.auto_clipboard": "自动监听剪贴板",
    "label.clear_after_typing": "输入后清空",
    "label.disable_hotkey_when_clipboard_empty": "剪贴板无文本时不接管快捷键",
    "label.toggle_ime_with_shift": "输入前后切换英文输入状态",
    "label.raw_clipboard_text": "原始剪贴板文本",
    "label.input_candidate_text": "待输入候选文本",
    "label.typing_mode": "模式",
    "label.typing_mode.default": "默认模式",
    "label.typing_mode.single_line": "单行模式",
    "label.typing_mode.split": "分裂模式",
    "label.single_line_replacement": "单行替换字符",
    "label.single_line_replacement.space": "空格",
    "label.single_line_replacement.tab": "Tab",
    "label.input_encoding": "输入编码",
    "label.output_encoding": "输出编码",
    "label.encoding.auto": "自动检测",
    "label.encoding.utf_8": "UTF-8",
    "label.encoding.utf_8_sig": "UTF-8 BOM",
    "label.encoding.gbk": "GBK",
    "label.encoding.big5": "Big5",
    "label.newline_backend": "底层换行实现",
    "label.newline_method.pynput": "pynput",
    "label.newline_method.win32_scan": "Win32 ScanCode",
    "label.newline_method.win32_vk": "Win32 VK",
    "label.newline_method.pyautogui": "pyautogui",
    "label.newline_method.keyboard": "keyboard",
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
    "label.developer_mode": "开发者模式",
    "label.developer_debug": "开发者调试",
    "label.debug_window_position": "窗口位置调试日志",
    "label.debug_newline_behavior": "换行行为调试日志",
    "label.export_debug_log": "导出调试日志",
    "label.clear_debug_log": "清空调试日志",
    "label.debug_log_count": "当前日志条数：{count}",
    "label.language": "语言",
    "label.apply": "应用",
    "label.restore_defaults": "恢复默认设置",
    "label.author": "作者",
    "label.project": "剪贴板转模拟输入工具",
    "label.github": "GitHub",
    "label.email": "Email",
    "label.contact_me": "联系我",
    "label.contact_email": "email",
    "label.contact_qq": "qq",
    "label.language.zh_cn": "中文",
    "label.language.en_us": "English",
    "status.starting": "启动中",
    "status.listening_hotkey": "监听中 · {hotkey}",
    "status.hotkey_failed": "快捷键注册失败，请更换",
    "status.input_hotkey_failed": "输入快捷键注册失败",
    "status.stop_hotkey_failed": "停止输入快捷键注册失败",
    "status.hotkey_toggle_failed": "热键开关快捷键注册失败",
    "status.hotkey_empty": "快捷键不能为空",
    "status.hotkey_applied": "快捷键已应用 · {hotkey}",
    "status.stop_hotkey_applied": "停止输入快捷键已应用 · {hotkey}",
    "status.hotkey_toggle_applied": "热键开关快捷键已应用 · {hotkey}",
    "status.hotkeys_enabled": "热键已启用",
    "status.hotkeys_disabled": "热键已禁用",
    "status.hotkey_released_empty": "剪贴板无文本，{hotkey} 已释放",
    "status.hotkey_registered": "快捷键已注册：{hotkey}",
    "status.typing_interval_mode_applied": "输入间隔模式已应用",
    "status.interval_saved": "输入间隔已保存",
    "status.interval_updated": "输入间隔已更新：{interval}ms",
    "status.interval_invalid": "输入间隔需在 0.1 到 10000 ms 之间",
    "status.target_duration_saved": "完成时间已保存",
    "status.target_duration_invalid": "完成时间必须在 1 到 10000ms 之间",
    "status.newline_method_updated": "底层换行实现已更新",
    "status.mode_updated": "模式已更新",
    "status.mode_applied": "模式已应用",
    "status.encoding_applied": "编码设置已应用",
    "status.split_position": "分裂模式：第 {current} / {total} 行",
    "status.split_finished": "分裂模式内容已全部输入",
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
    "status.contact_copied": "{item} 已复制",
    "status.contact_copy_failed": "复制失败：{error}",
    "status.window_hidden": "已最小化到托盘",
    "status.developer_mode_on": "开发者模式已开启",
    "status.developer_mode_off": "开发者模式已关闭",
    "status.debug_log_exported": "调试日志已导出",
    "status.debug_log_export_failed": "调试日志导出失败：{error}",
    "status.debug_log_cleared": "调试日志已清空",
    "status.debug_log_empty": "暂无调试日志",
    "tray.show_hide": "显示/隐藏窗口",
    "tray.exit": "退出",
    "help.body": "1. 复制文本后，原始剪贴板文本会进入上方文本框，待输入候选文本会进入下方文本框。\n2. 按输入快捷键，默认 Ctrl+V，即可将候选文本模拟为键盘输入。\n3. 模式包含默认、单行、分裂三种：默认模式模拟 Shift+Enter，单行模式替换换行，分裂模式每次输入一行。\n4. 输入间隔模式包含默认、自定义间隔、完成时间三种；极短完成时间可能受系统调度精度限制。\n5. 如果剪贴板为空，CVInput 会释放 Ctrl+V，避免影响系统原生粘贴。\n6. 如果目标程序以管理员权限运行，CVInput 也需要以管理员权限运行。\n7. 中文输入法下如出现中英混合输入异常，可开启“输入前后切换英文输入状态”。",
    "about.author": "Shrink",
    "about.description": "剪贴板转模拟输入工具",
    "about.usage_title": "使用说明",
    "about.notes_title": "注意事项",
    "about.notes": "微信、QQ 等聊天软件如果对自动换行不稳定，可使用单行模式或分裂模式。极短完成时间可能受系统调度精度限制；输入法切换依赖系统已安装英文输入法。",
    "about.long_description": "CVInput 是剪贴板转模拟输入工具。主界面采用双文本框架构：上方保留原始剪贴板文本，下方显示待输入候选文本，实际输入只读取候选文本。\n\n三种输入模式：默认模式保留换行并模拟 Shift+Enter；单行模式把换行替换为空格或 Tab；分裂模式按行拆分，每次快捷键只输入一行。\n\n输入间隔模式包含默认模式、自定义间隔模式和完成时间模式。完成时间模式会根据文本长度动态计算每字符间隔，使本次输入尽量在指定时间内完成。\n\n支持输入前切换英文输入法、输入后恢复原输入法；也支持开发者模式、窗口与换行调试日志导出。",
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
