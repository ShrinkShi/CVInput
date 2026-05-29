# 打包说明

[返回 README](../README.md)

CVInput 使用 PyInstaller 打包为 Windows 可执行文件。

## 前置环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install pyinstaller
```

## 打包命令

```powershell
pyinstaller CVInput.spec
```

产物默认输出到：

```text
dist/CVInput.exe
```

## 资源文件

| 资源 | 用途 |
|---|---|
| `icon.ico` | EXE 与任务栏图标 |
| `assets/icon/icon256.png` | 托盘与运行时图标 |
| `assets/icon/icon512.png` | 托盘与运行时图标 |
| `src/locales/*.json` | 多语言文件 |
| `assets/*.png` | 主窗口、设置、关于、托盘相关图标 |

## 注意事项

- `dist/` 和 `build/` 通常不提交到仓库。
- 如果任务栏图标异常，优先检查 `icon.ico` 是否位于仓库根目录。
- 如果托盘图标异常，优先检查 `assets/icon/icon256.png` 和 `assets/icon/icon512.png` 是否被打包。
- 如果语言文件丢失，检查 `CVInput.spec` 中是否包含 `src/locales`。
