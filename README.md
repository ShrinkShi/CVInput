<p align="center">
  <img src="assets/readme/cover.svg" alt="CVInput" width="820">
</p>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/ShrinkShi/CVInput/stargazers"><img alt="stars" src="https://img.shields.io/github/stars/ShrinkShi/CVInput?style=flat&logo=github&label=stars"></a>
  <a href="https://github.com/ShrinkShi/CVInput/network/members"><img alt="forks" src="https://img.shields.io/github/forks/ShrinkShi/CVInput?style=flat&logo=github&label=forks"></a>
  <img alt="version" src="https://img.shields.io/badge/version-v1.1.0-4f947f">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows-0078D4">
  <img alt="python" src="https://img.shields.io/badge/python-3.10%2B-3776AB">
  <img alt="license" src="https://img.shields.io/badge/license-TODO-lightgrey">
</p>

# CVInput

CVInput 是一个 Windows 桌面工具，用于把剪贴板文本转换为模拟键盘输入。

它适合目标程序不接受普通粘贴、需要逐字输入，或聊天软件中需要降低回车误发送风险的场景。

> 使用边界：CVInput 通过模拟键盘事件工作，不等价于系统原生粘贴。不同目标程序对模拟按键的处理可能不同，尤其是微信、QQ、Electron、Chromium、Qt 类输入框。

## 核心特性

- 双文本框架构：保留原始剪贴板文本，同时生成待输入候选文本。
- 三种输入模式：默认模式、单行模式、分裂模式。
- 三种输入间隔模式：默认、自定义间隔、完成时间。
- 全局输入快捷键，默认 `Ctrl+V`；输入中再次按停止快捷键可停止输入。
- 多槽位输入，支持 `Alt+1` 到 `Alt+0` 输入预设内容。
- 输入前自动切换英文输入法，输入后恢复原输入法。
- 支持窗口置顶、透明度、最小化到托盘、开机自启。
- 支持开发者模式、调试日志导出与清空。
- 支持多语言，语言文件位于 `src/locales/`。

## 技术栈

| 层级 | 技术 |
|---|---|
| 语言 | Python 3.10+ |
| GUI | CustomTkinter / Tkinter |
| 输入模拟 | pynput、pyautogui、keyboard、Win32 SendInput |
| 剪贴板 | pyperclip |
| Windows 能力 | pywin32、全局热键、IME 布局切换、DPI awareness |
| 托盘与图标 | pystray、Pillow |
| 打包 | PyInstaller |

更多细节见：[技术栈说明](docs/TECH_STACK.md)。

## 快速开始

前置环境：

- Windows 10/11
- Python 3.10+
- 可选：英语美国输入法布局，用于输入前自动切换英文输入状态

```powershell
git clone https://github.com/ShrinkShi/CVInput.git
cd CVInput
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

验证方式：

1. 复制一段文本。
2. 打开 CVInput，确认候选文本框已有内容。
3. 聚焦目标输入框。
4. 按 `Ctrl+V` 触发模拟输入。

## 使用方法

### 基本流程

1. 复制文本，或点击主界面的读取剪贴板按钮。
2. 在原始剪贴板文本框中确认原文。
3. 在待输入候选文本框中确认实际将要输入的内容。
4. 聚焦目标窗口的输入框。
5. 按输入快捷键，默认 `Ctrl+V`。
6. 如果需要停止输入，再次按停止快捷键，默认同样是 `Ctrl+V`。

### 输入模式

| 模式 | 内部值 | 行为 | 适用场景 |
|---|---|---|---|
| 默认模式 | `default` | 保留换行，输入时模拟 `Shift+Enter` | 普通文本框、编辑器、支持 `Shift+Enter` 换行的输入框 |
| 单行模式 | `single_line` | 把换行替换为空格或 `Tab` | AI 输入框、搜索框、聊天框、命令框 |
| 分裂模式 | `split` | 按行拆分剪贴板，每次快捷键只输入一行 | 微信、QQ 等回车可能发送消息的输入框 |

### 输入间隔模式

| 模式 | 内部值 | 行为 |
|---|---|---|
| 默认模式 | `default` | 使用项目默认字符间隔 |
| 自定义间隔模式 | `custom_interval` | 使用固定字符间隔，单位毫秒 |
| 完成时间模式 | `target_duration` | 根据本次实际输入文本长度动态计算字符间隔 |

极短完成时间会受到 Windows 调度精度、目标程序响应速度和输入法状态影响，不保证严格精确。

## 配置说明

配置文件默认位置：

```text
%LOCALAPPDATA%\CVInput\config.json
```

常用配置项：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `input_hotkey` | `Ctrl+V` | 输入快捷键 |
| `stop_typing_hotkey` | `Ctrl+V` | 输入中停止快捷键 |
| `hotkey_toggle_hotkey` | `Ctrl+Alt+V` | 热键开关快捷键 |
| `input_mode` | `default` | 输入模式 |
| `typing_interval_mode` | `default` | 输入间隔模式 |
| `auto_clipboard` | `true` | 是否自动监听剪贴板 |
| `toggle_ime_with_shift` | `true` | 输入前后是否切换英文输入状态 |
| `close_to_tray` | `true` | 关闭窗口时是否最小化到托盘 |
| `developer_mode` | `false` | 是否开启开发者模式 |

如果关闭“下次启动时记住设置项”，程序只保存该开关状态，其余配置下次启动恢复默认。

## 更多文档

- [技术栈说明](docs/TECH_STACK.md)
- [开发说明与项目结构](docs/DEVELOPMENT.md)
- [开发者调试](docs/DEBUGGING.md)
- [打包说明](docs/BUILD.md)

## 常见问题

### 为什么微信或 QQ 中默认模式换行不稳定？

默认模式依赖模拟 `Shift+Enter`。部分聊天软件不会把模拟按键当成真实用户按键处理，或者会在前端事件层做特殊判断。建议改用单行模式或分裂模式。

### 为什么 `Ctrl+V` 有时会恢复成系统粘贴？

当候选文本为空，并且开启“剪贴板无文本时不接管快捷键”时，CVInput 会释放输入快捷键，避免影响系统原生粘贴。

### 为什么目标程序收不到输入？

常见原因：

- 目标窗口没有获得焦点；
- 目标程序以管理员权限运行，而 CVInput 没有；
- 全局热键被其他软件占用；
- 目标程序对模拟键盘事件做了限制。

### 中文输入异常怎么办？

可以开启“输入前后切换英文输入状态”。该功能会在输入前尝试切到英文输入法，输入后恢复原输入法。

## 贡献

欢迎通过 Issue 反馈问题或建议：

<https://github.com/ShrinkShi/CVInput/issues>

本地检查：

```powershell
python -m compileall -q main.py src
python main.py
```

## 许可证

TODO: 仓库当前未提供 `LICENSE` 文件。添加许可证前，不应假设本项目使用 MIT、Apache-2.0、GPL 或其他开源协议。

## 使用边界

CVInput 是模拟输入辅助工具。请在你有权限操作的程序和文本框中使用。用户需要自行承担目标程序风控、账号策略、权限环境和误输入带来的后果。

作者：Shrink
