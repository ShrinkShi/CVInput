# 技术栈

[返回 README](../README.md)

CVInput 是一个 Windows 桌面应用，核心由 Python、CustomTkinter、全局热键、剪贴板监听和模拟键盘输入组成。

## 运行环境

| 项目 | 说明 |
|---|---|
| 操作系统 | Windows 10/11 |
| Python | 建议 Python 3.10+ |
| GUI | CustomTkinter / Tkinter |
| 配置存储 | `%LOCALAPPDATA%\CVInput\config.json` |
| 打包方式 | PyInstaller |

## 主要依赖

| 依赖 | 用途 |
|---|---|
| `customtkinter` | 主界面、设置窗口、关于窗口、自定义控件 |
| `pynput` | 键盘模拟和部分热键释放 |
| `pyperclip` | 剪贴板读取与写入 |
| `pystray` | 系统托盘图标与右键菜单 |
| `pillow` | 图标读取、托盘图标处理 |
| `pywin32` | Windows 输入法切换、窗口布局读取 |
| `pyautogui` | 默认模式下的 `Shift+Enter` 模拟实现之一 |
| `keyboard` | 开发者实验项中的底层换行实现 |

## Windows 能力

| 能力 | 实现位置 | 说明 |
|---|---|---|
| DPI awareness | `src/dpi.py` | 启动最早阶段声明，避免 Tk/CTk 坐标虚拟化 |
| 全局热键 | `src/hotkey.py` | 注册输入、停止、热键开关、多槽位快捷键 |
| Win32 输入 | `src/win_input.py` | `SendInput` 辅助，用于 Unicode 字符和部分按键模拟 |
| 输入法切换 | `src/ime.py` | 读取目标窗口键盘布局，输入前切英文，输入后恢复 |
| 开机自启 | `src/startup.py` | 写入当前用户 Run 注册表项 |

## UI 架构

| 模块 | 说明 |
|---|---|
| `src/ui/main_ui.py` | 主窗口，双文本框、按钮、进度条、多槽位入口 |
| `src/ui/settings_mixin.py` | 设置窗口和开发者调试窗口 |
| `src/ui/about_mixin.py` | 关于窗口和联系我窗口 |
| `src/ui/window_utils.py` | 子窗口贴靠定位工具 |
| `src/ui/widgets.py` | 图标、下拉菜单、应用图标、通用控件辅助 |

## 输入链路

```text
全局热键 / 输入按钮
  -> TypingController.start_typing()
  -> TypingController._typing_worker()
  -> maybe_toggle_ime_before_typing()
  -> TypingEngine.type_text()
  -> restore_ime_after_typing()
```

候选文本在进入 `TypingEngine` 前已经由当前模式处理。默认模式保留换行，单行模式替换换行，分裂模式每次只输入当前行。
