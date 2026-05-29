# CVInput

[中文](README.md) | [English](README_EN.md)

CVInput 是一个 Windows 桌面工具，用于把剪贴板文本转换为模拟键盘输入。

它适合以下场景：

- 目标程序不接受普通粘贴；
- 需要逐字模拟输入；
- 聊天软件中需要降低回车误发送风险；
- 需要把多行文本拆成单行或逐行输入；
- 需要调试窗口定位、换行行为、输入法切换等输入问题。

> 使用边界：CVInput 通过模拟键盘事件工作，不等价于系统原生粘贴。不同目标程序对模拟按键的处理可能不同，尤其是微信、QQ、Electron、Chromium、Qt 类输入框。

当前版本：`v1.1.0`

## 项目简介

CVInput 监听或读取剪贴板文本，并将文本放入主界面的双文本框：

- **原始剪贴板文本**：保留剪贴板原文，方便确认输入来源。
- **待输入候选文本**：根据当前模式处理后，真正参与模拟输入。

用户按下输入快捷键后，程序会把候选文本逐字符输入到当前目标窗口。默认输入快捷键是 `Ctrl+V`。

## 核心特性

- 剪贴板自动监听与手动读取。
- 默认、单行、分裂三种输入模式。
- 默认、自定义间隔、完成时间三种输入间隔模式。
- 输入快捷键、停止快捷键、热键开关快捷键可配置。
- 输入中再次按停止快捷键可停止输入。
- 10 个多槽位输入，默认快捷键为 `Alt+1` 到 `Alt+0`。
- 输入前切换英文输入法，输入后恢复原输入法。
- 窗口置顶、透明度、最小化到托盘、开机自启。
- 开发者模式、分类调试日志、日志导出。
- 多语言界面，语言文件位于 `src/locales/`。

## 效果预览

TODO: 补充主界面、设置窗口、开发者调试窗口截图。

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

### 输入法切换

设置项“输入前后切换英文输入状态”开启后，程序会：

1. 获取当前前台目标窗口。
2. 记录目标窗口当前输入法布局。
3. 尝试切换到英语美国布局 `0x0409`。
4. 输入完成后恢复原布局。

该功能依赖 Windows、`pywin32` 和系统中已安装的英文输入法。如果目标程序以管理员权限运行，CVInput 也可能需要以管理员权限运行。

## 配置说明

配置文件默认位置：

```text
%LOCALAPPDATA%\CVInput\config.json
```

如果关闭“下次启动时记住设置项”，程序只保存该开关状态，其余配置下次启动恢复默认。

### 常用配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `input_hotkey` | `Ctrl+V` | 输入快捷键 |
| `stop_typing_hotkey` | `Ctrl+V` | 输入中停止快捷键 |
| `hotkey_toggle_hotkey` | `Ctrl+Alt+V` | 热键开关快捷键 |
| `hotkeys_enabled` | `true` | 是否启用全局热键 |
| `auto_clipboard` | `true` | 是否自动监听剪贴板 |
| `disable_hotkey_when_clipboard_empty` | `true` | 候选文本为空时释放输入快捷键 |
| `clear_after_input` | `false` | 输入完成后是否清空文本 |
| `multi_slot_enabled` | `true` | 是否显示多槽位输入 |
| `always_on_top` | `true` | 主窗口是否置顶 |
| `close_to_tray` | `true` | 关闭窗口时是否最小化到托盘 |
| `startup_on_boot` | `false` | 是否开机自启 |

### 输入配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `input_mode` | `default` | 输入模式 |
| `single_line_replacement` | `space` | 单行模式换行替换字符，可选 `space` / `tab` |
| `typing_interval_mode` | `default` | 输入间隔模式 |
| `typing_interval_ms` | `30` | 自定义间隔模式下的字符间隔 |
| `typing_target_duration_ms` | `1000` | 完成时间模式的目标总时长 |
| `toggle_ime_with_shift` | `true` | 输入前后是否切换英文输入状态 |
| `newline_shift_enter_method` | `pyautogui` | 默认模式下底层 `Shift+Enter` 实现 |
| `input_encoding` | `auto` | 输入文本解码方式 |
| `output_encoding` | `utf-8` | 日志导出编码 |

### 开发者调试配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `developer_mode` | `false` | 是否开启开发者模式 |
| `debug_window_position` | `false` | 是否记录窗口位置日志 |
| `debug_newline_behavior` | `false` | 是否记录换行、输入、IME 日志 |

## 开发者模式

开启开发者模式后，设置窗口旁会出现开发者调试窗口。

可用日志分类：

- 窗口位置调试日志：记录设置、关于等子窗口的尺寸、坐标、DPI 和跟随移动数据。
- 换行行为调试日志：记录输入模式、换行处理、底层 `Shift+Enter` 模拟、IME 切换等数据。

调试日志保存在内存中，可从设置窗口导出为文本文件。

## 多语言

当前仓库包含以下语言文件：

| 代码 | 显示名称 |
|---|---|
| `zh_cn` | 简体中文 |
| `en_us` | English |
| `zh_tw` | 繁體中文 |
| `ru_ru` | Русский |
| `ko_kp` | 한국어 |

新增语言时，在 `src/locales/` 下添加对应 JSON 文件即可。

## 打包

使用 PyInstaller：

```powershell
python -m pip install pyinstaller
pyinstaller CVInput.spec
```

资源说明：

| 资源 | 说明 |
|---|---|
| `icon.ico` | Windows EXE / 任务栏图标 |
| `assets/icon/icon256.png` | 托盘与运行时图标 |
| `assets/icon/icon512.png` | 托盘与运行时图标 |
| `src/locales/*.json` | 多语言资源 |

打包产物位于 `dist/`，通常不提交到仓库。

## 项目结构

```text
.
├── main.py              # 程序入口，最早声明 DPI awareness
├── src/
│   ├── app/             # 应用控制器：热键、剪贴板、输入、设置、托盘、生命周期
│   ├── ui/              # CustomTkinter 界面、窗口、设置、关于页、控件
│   ├── locales/         # 多语言 JSON 文件
│   ├── typing_engine.py # 模拟输入核心
│   ├── ime.py           # Windows 输入法切换
│   ├── win_input.py     # Win32 SendInput 辅助
│   └── debug_logger.py  # 开发者调试日志
├── assets/              # UI 图标资源
├── requirements.txt     # Python 依赖
└── CVInput.spec         # PyInstaller 打包配置
```

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

### 调试日志在哪里？

开启开发者模式后，在开发者调试窗口中打开对应日志分类，然后使用“导出调试日志”按钮导出。

## 贡献指南

欢迎通过 Issue 反馈问题或建议：

<https://github.com/ShrinkShi/CVInput/issues>

本地开发建议：

```powershell
python -m compileall -q main.py src
python main.py
```

提交 PR 前建议说明：

- 修改目的；
- 影响的功能区域；
- 已执行的测试；
- 是否涉及全局热键、输入法切换、托盘、窗口定位等高风险逻辑。

## 许可证

TODO: 仓库当前未提供 `LICENSE` 文件。添加许可证前，不应假设本项目使用 MIT、Apache-2.0、GPL 或其他开源协议。

## 使用边界

CVInput 是模拟输入辅助工具。请在你有权限操作的程序和文本框中使用。用户需要自行承担目标程序风控、账号策略、权限环境和误输入带来的后果。

## 相关链接

- Issues：<https://github.com/ShrinkShi/CVInput/issues>
- English README：<README_EN.md>

作者：Shrink
