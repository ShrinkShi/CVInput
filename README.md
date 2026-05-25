# CVInput

CVInput 是一个 Windows 桌面小工具，用于把剪贴板文本转换为逐字符模拟输入。复制文本后，程序会自动读取剪贴板内容并显示在小窗口中；点击目标输入框后，按全局快捷键或点击输入图标即可把文本逐字符输入到当前焦点窗口。

## 特点

- 使用 `customtkinter` 构建小尺寸、深色、无边框自定义标题栏界面。
- 默认全局快捷键为 `Ctrl+V`，支持自定义快捷键。
- 使用 Windows 原生 `RegisterHotKey` + `GetMessageW` 监听全局快捷键。
- 使用 `pyperclip` 后台轮询剪贴板。
- 使用 `pynput.keyboard.Controller` 逐字符模拟输入，支持中文、英文和常见符号。
- 支持系统托盘、关闭时最小化到托盘、托盘显示/隐藏窗口和托盘退出。
- 支持开机自启、窗口置顶、透明度、输入后清空和中英文语言切换。

## 安装依赖

建议使用 Python 3.10 或 3.11，在 Windows 上运行：

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 运行方式

```bash
python main.py
```

运行后窗口默认置顶，默认会自动监听剪贴板，并在系统托盘创建图标。

## 打包方式

```bash
python -m PyInstaller --onefile --windowed --name CVInput --icon assets/icon.ico --add-data "cvinput/locales;cvinput/locales" main.py
```

打包产物会生成到 `dist/`，构建缓存会生成到 `build/`。这些目录不应提交到仓库。

## 默认快捷键

默认快捷键是：

```text
Ctrl+V
```

当 CVInput 成功注册 `Ctrl+V` 时，按下 `Ctrl+V` 不再执行目标程序自己的粘贴动作，而是触发 CVInput 的逐字符模拟输入。输入前程序会释放触发快捷键的按键，避免 `Ctrl`、`Alt` 等修饰键残留影响后续输入。

## 如何修改快捷键

点击标题栏左侧的设置图标，打开相对主窗口定位的设置弹窗。在“快捷键”输入框里填写新的快捷键，然后点击输入框右侧的应用图标。

支持的示例：

```text
Ctrl+V
Ctrl+Alt+V
Ctrl+Alt+S
Alt+V
Shift+F8
Ctrl+Shift+Enter
```

支持的修饰键：

- `Ctrl` / `Control`
- `Alt`
- `Shift`
- `Win` / `Windows` / `Meta`

支持的主键包括 `A-Z`、`0-9`、`F1-F24`、`Enter`、`Tab`、`Space`、`Esc`、`Home`、`End`、`PageUp`、`PageDown`、`Delete`、`Backspace` 和方向键。

## 托盘与关闭行为

程序运行时会创建系统托盘图标，托盘菜单包含：

- 显示/隐藏窗口
- 退出

如果开启“关闭时最小化到托盘”，点击主窗口关闭按钮只会隐藏窗口，快捷键和剪贴板监听继续运行。此时需要通过托盘菜单“退出”才会真正关闭程序。

如果关闭该选项，点击关闭按钮会直接退出程序，并注销全局快捷键、停止剪贴板后台线程和托盘图标。

## 开机自启

设置中的“开机自启”使用当前用户的注册表 Run 项：

```text
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

开启时写入 `CVInput` 项，关闭时删除该项。操作失败时程序会在状态栏提示，不会崩溃。

## 语言切换

设置中可以在中文和英文之间切换。语言文件位于：

```text
cvinput/locales/zh_cn.json
cvinput/locales/en_us.json
```

缺失语言 key 时会回退到中文默认值或 key 本身，不会导致程序崩溃。

## 快捷键注册失败怎么办

Windows 全局快捷键同一时间只能被一个程序注册。如果 `Ctrl+V` 或你设置的其他快捷键已经被系统、输入法、远程桌面软件、安全软件或其他程序占用，CVInput 就无法注册该快捷键。

注册失败时程序不会崩溃，状态栏会提示“快捷键注册失败，请更换”。此时仍可点击输入图标手动触发输入，也可以打开设置，把快捷键改成 `Ctrl+Alt+V`、`Ctrl+Alt+S`、`Alt+V` 等组合。

## 为什么某些目标窗口需要管理员权限

Windows 有权限隔离机制：普通权限运行的程序通常不能向管理员权限运行的窗口发送模拟键盘输入。例如，目标窗口是以管理员身份启动的命令行、安装器或系统管理工具时，普通权限的 CVInput 可能无法输入。

如果需要向管理员权限的目标窗口模拟输入，请右键以管理员身份运行 CVInput，使 CVInput 和目标窗口处于相同或更高权限级别。

## 项目结构

```text
CVInput/
├─ main.py
├─ cvinput/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ ui_ctk.py
│  ├─ hotkey.py
│  ├─ clipboard.py
│  ├─ typing_engine.py
│  ├─ config.py
│  ├─ constants.py
│  ├─ i18n.py
│  ├─ tray.py
│  ├─ startup.py
│  └─ locales/
│     ├─ zh_cn.json
│     └─ en_us.json
├─ assets/
│  └─ icon.ico
├─ requirements.txt
└─ README.md
```

职责说明：

- `main.py`：程序入口，只创建并启动 `CVInputApp`。
- `cvinput/app.py`：组合 UI、快捷键、剪贴板、输入引擎、托盘和配置，负责生命周期。
- `cvinput/ui_ctk.py`：customtkinter 无边框主界面、设置弹窗和关于弹窗。
- `cvinput/hotkey.py`：Windows `RegisterHotKey` 全局快捷键监听。
- `cvinput/clipboard.py`：`pyperclip` 剪贴板轮询。
- `cvinput/typing_engine.py`：`pynput` 逐字符模拟输入。
- `cvinput/config.py`：JSON 配置读写。
- `cvinput/i18n.py`：语言文件加载与 fallback。
- `cvinput/tray.py`：系统托盘图标与菜单。
- `cvinput/startup.py`：Windows Run 项开机自启。

## 使用建议

1. 复制要输入的文本。
2. 确认 CVInput 文本框里已经显示该文本。
3. 点击目标程序的输入框，使目标输入框获得焦点。
4. 按 `Ctrl+V` 或你设置的快捷键。
5. 如需中断输入，点击停止图标。

## 注意事项

- 输入过程中不要切换焦点，否则文本会继续输入到新的焦点窗口。
- 如果要手动编辑 CVInput 文本框，程序在文本框获得焦点时不会用剪贴板内容覆盖它。
- 默认输入间隔为 `0.03` 秒，可在设置中调整。
- 托盘“退出”和关闭按钮的行为不同：开启“关闭时最小化到托盘”后，关闭按钮只隐藏窗口，托盘“退出”才会释放资源并结束程序。
