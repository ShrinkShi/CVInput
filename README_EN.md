# CVInput

[中文](README.md) | [English](README_EN.md)

CVInput is a Windows desktop utility that converts clipboard text into simulated keyboard input.

It is useful when:

- the target application does not accept normal paste;
- text must be typed character by character;
- chat applications may send messages when Enter is triggered;
- multi-line text needs to be converted to single-line or typed line by line;
- input behavior, window positioning, IME switching, or newline handling needs debugging.

> Boundary: CVInput works by simulating keyboard events. It is not the same as native clipboard paste. Different target applications may handle simulated keys differently, especially WeChat, QQ, Electron, Chromium, and Qt-based input fields.

Current version: `v1.1.0`

## Overview

CVInput monitors or reads clipboard text and displays it in a two-textbox workflow:

- **Raw clipboard text**: preserves the original clipboard content.
- **Input candidate text**: processed by the selected mode and used for actual simulated typing.

When the user presses the input hotkey, CVInput types the candidate text character by character into the current target window. The default input hotkey is `Ctrl+V`.

## Features

- Automatic clipboard monitoring and manual clipboard reading.
- Three input modes: Default, Single-line, and Split.
- Three typing interval modes: Default, Custom interval, and Target duration.
- Configurable input hotkey, stop hotkey, and hotkey toggle hotkey.
- Press the stop hotkey while typing to stop input.
- 10 input slots, default hotkeys `Alt+1` to `Alt+0`.
- Switch to English input layout before typing and restore the previous layout after typing.
- Always-on-top, opacity control, tray minimization, and startup on boot.
- Developer mode, category-based debug logs, and log export.
- Multi-language UI. Locale files are stored in `src/locales/`.

## Preview

TODO: Add screenshots for the main window, settings window, and developer debug panel.

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

### IME Switching

When "switch to English input state before and after typing" is enabled, CVInput will:

1. Get the current foreground target window.
2. Record its current keyboard layout.
3. Try to switch to the English US layout `0x0409`.
4. Restore the previous layout after typing.

This feature depends on Windows, `pywin32`, and an installed English input layout. If the target application runs as administrator, CVInput may also need to run as administrator.

## Configuration

Default config path:

```text
%LOCALAPPDATA%\CVInput\config.json
```

If "remember settings next time" is disabled, CVInput only saves that switch state and resets other settings on next launch.

### Common Settings

| Key | Default | Description |
|---|---|---|
| `input_hotkey` | `Ctrl+V` | Input hotkey |
| `stop_typing_hotkey` | `Ctrl+V` | Stop hotkey while typing |
| `hotkey_toggle_hotkey` | `Ctrl+Alt+V` | Hotkey toggle hotkey |
| `hotkeys_enabled` | `true` | Whether global hotkeys are enabled |
| `auto_clipboard` | `true` | Whether clipboard monitoring is enabled |
| `disable_hotkey_when_clipboard_empty` | `true` | Release the input hotkey when candidate text is empty |
| `clear_after_input` | `false` | Clear text after typing finishes |
| `multi_slot_enabled` | `true` | Show multi-slot input |
| `always_on_top` | `true` | Keep the main window always on top |
| `close_to_tray` | `true` | Minimize to tray when closing the window |
| `startup_on_boot` | `false` | Start with Windows |

### Input Settings

| Key | Default | Description |
|---|---|---|
| `input_mode` | `default` | Input mode |
| `single_line_replacement` | `space` | Replacement for line breaks in Single-line mode: `space` or `tab` |
| `typing_interval_mode` | `default` | Typing interval mode |
| `typing_interval_ms` | `30` | Per-character interval in Custom interval mode |
| `typing_target_duration_ms` | `1000` | Target total duration in Target duration mode |
| `toggle_ime_with_shift` | `true` | Switch to English input layout before typing and restore afterward |
| `newline_shift_enter_method` | `pyautogui` | Low-level `Shift+Enter` backend in Default mode |
| `input_encoding` | `auto` | Input text decoding mode |
| `output_encoding` | `utf-8` | Debug log export encoding |

### Developer Debug Settings

| Key | Default | Description |
|---|---|---|
| `developer_mode` | `false` | Enable developer mode |
| `debug_window_position` | `false` | Record window positioning logs |
| `debug_newline_behavior` | `false` | Record newline, typing, and IME logs |

## Developer Mode

Developer mode shows a developer debug panel next to the settings window.

Available log categories:

- Window position logs: popup size, coordinates, DPI, and follow-movement data.
- Newline behavior logs: input mode, newline handling, low-level `Shift+Enter`, and IME switching data.

Debug logs are stored in memory and can be exported from the settings window.

## Languages

Current locale files:

| Code | Display name |
|---|---|
| `zh_cn` | 简体中文 |
| `en_us` | English |
| `zh_tw` | 繁體中文 |
| `ru_ru` | Русский |
| `ko_kp` | 한국어 |

To add a language, add a JSON file under `src/locales/`.

## Build

Build with PyInstaller:

```powershell
python -m pip install pyinstaller
pyinstaller CVInput.spec
```

Resources:

| Resource | Description |
|---|---|
| `icon.ico` | Windows EXE / taskbar icon |
| `assets/icon/icon256.png` | Tray/runtime icon |
| `assets/icon/icon512.png` | Tray/runtime icon |
| `src/locales/*.json` | Locale files |

The build output is generated under `dist/`, which is normally not committed.

## Project Structure

```text
.
├── main.py              # Entry point; declares DPI awareness first
├── src/
│   ├── app/             # Controllers: hotkeys, clipboard, typing, settings, tray, lifecycle
│   ├── ui/              # CustomTkinter UI, windows, settings, about page, widgets
│   ├── locales/         # Language JSON files
│   ├── typing_engine.py # Simulated typing core
│   ├── ime.py           # Windows IME switching
│   ├── win_input.py     # Win32 SendInput helpers
│   └── debug_logger.py  # Developer debug logger
├── assets/              # UI icon resources
├── requirements.txt     # Python dependencies
└── CVInput.spec         # PyInstaller build config
```

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

### Where are debug logs?

Enable Developer mode, turn on the needed log category in the developer debug panel, and use "Export debug log" in settings.

## Contributing

Issues and suggestions are welcome:

<https://github.com/ShrinkShi/CVInput/issues>

Recommended local checks:

```powershell
python -m compileall -q main.py src
python main.py
```

When submitting a PR, include:

- the purpose of the change;
- affected feature areas;
- tests performed;
- whether it touches high-risk areas such as global hotkeys, IME switching, tray behavior, or window positioning.

## License

TODO: This repository currently does not include a `LICENSE` file. Do not assume MIT, Apache-2.0, GPL, or any other open-source license until one is added.

## Use Boundary

CVInput is an input automation helper. Use it only in applications and input fields where you have permission to operate. Users are responsible for target application policies, account risk, permission environments, and unintended input.

## Links

- Issues: <https://github.com/ShrinkShi/CVInput/issues>
- 中文 README: <README.md>

Author: Shrink
