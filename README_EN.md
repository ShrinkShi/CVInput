<p align="center">
  <img src="assets/readme/cover.png" alt="CVInput" width="820">
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

CVInput is a Windows desktop utility that converts clipboard text into simulated keyboard input.

It is useful when the target application does not accept normal paste, text must be typed character by character, or chat applications may send messages when Enter is triggered.

> Boundary: CVInput works by simulating keyboard events. It is not the same as native clipboard paste. Different target applications may handle simulated keys differently, especially WeChat, QQ, Electron, Chromium, and Qt-based input fields.

## Features

- Two-textbox workflow: keep raw clipboard text and generate actual input candidate text.
- Three input modes: Default, Single-line, and Split.
- Three typing interval modes: Default, Custom interval, and Target duration.
- Global input hotkey, default `Ctrl+V`; press the stop hotkey while typing to stop input.
- Multi-slot input with `Alt+1` to `Alt+0`.
- Switch to English input layout before typing and restore the previous layout after typing.
- Always-on-top, opacity control, tray minimization, and startup on boot.
- Developer mode with debug log export and clearing.
- Multi-language UI. Locale files are stored in `src/locales/`.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| GUI | CustomTkinter / Tkinter |
| Input simulation | pynput, pyautogui, keyboard, Win32 SendInput |
| Clipboard | pyperclip |
| Windows integration | pywin32, global hotkeys, IME layout switching, DPI awareness |
| Tray and icons | pystray, Pillow |
| Packaging | PyInstaller |

More details: [Tech Stack](docs/TECH_STACK.md).

## Quick Start

Requirements:

- Windows 10/11
- Python 3.10+
- Optional: English US keyboard layout, used by automatic IME switching

```powershell
git clone https://github.com/ShrinkShi/CVInput.git
cd CVInput
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Basic verification:

1. Copy some text.
2. Open CVInput and confirm the candidate textbox contains content.
3. Focus the target input field.
4. Press `Ctrl+V` to start simulated typing.

## Usage

### Basic Flow

1. Copy text, or click the manual clipboard read button.
2. Confirm the content in the raw clipboard textbox.
3. Confirm the actual text to be typed in the input candidate textbox.
4. Focus the target application's input field.
5. Press the input hotkey, default `Ctrl+V`.
6. Press the stop hotkey to stop typing if needed. By default it is also `Ctrl+V`.

### Input Modes

| Mode | Internal value | Behavior | Good for |
|---|---|---|---|
| Default | `default` | Keeps line breaks and simulates `Shift+Enter` | Regular text boxes, editors, inputs that support `Shift+Enter` newlines |
| Single-line | `single_line` | Replaces line breaks with spaces or `Tab` | AI inputs, search boxes, chat inputs, command boxes |
| Split | `split` | Splits clipboard text by line and types one line per hotkey press | WeChat, QQ, and other inputs where Enter may send messages |

### Typing Interval Modes

| Mode | Internal value | Behavior |
|---|---|---|
| Default | `default` | Uses the project default per-character interval |
| Custom interval | `custom_interval` | Uses a fixed per-character interval in milliseconds |
| Target duration | `target_duration` | Calculates the per-character interval from the actual text length |

Very short target durations are limited by Windows scheduling precision, target application responsiveness, and IME state.

## Configuration

Default config path:

```text
%LOCALAPPDATA%\CVInput\config.json
```

Common settings:

| Key | Default | Description |
|---|---|---|
| `input_hotkey` | `Ctrl+V` | Input hotkey |
| `stop_typing_hotkey` | `Ctrl+V` | Stop hotkey while typing |
| `hotkey_toggle_hotkey` | `Ctrl+Alt+V` | Hotkey toggle hotkey |
| `input_mode` | `default` | Input mode |
| `typing_interval_mode` | `default` | Typing interval mode |
| `auto_clipboard` | `true` | Whether clipboard monitoring is enabled |
| `toggle_ime_with_shift` | `true` | Switch to English input layout before typing and restore afterward |
| `close_to_tray` | `true` | Minimize to tray when closing the window |
| `developer_mode` | `false` | Enable developer mode |

If "remember settings next time" is disabled, CVInput only saves that switch state and resets other settings on next launch.

## More Documentation

- [Tech Stack](docs/TECH_STACK.md)
- [Development and Project Structure](docs/DEVELOPMENT.md)
- [Developer Debugging](docs/DEBUGGING.md)
- [Build Guide](docs/BUILD.md)

## FAQ

### Why are newlines unreliable in WeChat or QQ default mode?

Default mode relies on simulated `Shift+Enter`. Some chat applications do not handle simulated keys like real user key events, or they apply special frontend event handling. Use Single-line mode or Split mode instead.

### Why does `Ctrl+V` sometimes behave like native paste again?

When candidate text is empty and "do not capture hotkey when clipboard has no text" is enabled, CVInput releases the input hotkey to avoid blocking native paste.

### Why does the target application not receive input?

Common causes:

- the target window is not focused;
- the target application runs as administrator while CVInput does not;
- the global hotkey conflicts with another application;
- the target application restricts simulated keyboard events.

### What should I do if Chinese input behaves incorrectly?

Enable "switch to English input state before and after typing". CVInput will try to switch to English before typing and restore the previous layout afterward.

## Contributing

Issues and suggestions are welcome:

<https://github.com/ShrinkShi/CVInput/issues>

Local checks:

```powershell
python -m compileall -q main.py src
python main.py
```

## License

TODO: This repository currently does not include a `LICENSE` file. Do not assume MIT, Apache-2.0, GPL, or any other open-source license until one is added.

## Use Boundary

CVInput is an input automation helper. Use it only in applications and input fields where you have permission to operate. Users are responsible for target application policies, account risk, permission environments, and unintended input.

Author: Shrink
