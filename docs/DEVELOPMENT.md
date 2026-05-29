# 开发说明

[返回 README](../README.md)

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
├── docs/                # README 拆分文档
├── requirements.txt     # Python 依赖
└── CVInput.spec         # PyInstaller 打包配置
```

## 本地开发

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 基础检查

```powershell
python -m compileall -q main.py src
```

## 高风险区域

以下区域修改后需要重点人工验证：

- 全局热键注册与释放；
- 输入中停止逻辑；
- 默认、单行、分裂模式；
- 输入前后切换英文输入法；
- 子窗口定位与 DPI 缩放；
- 托盘显示、隐藏、退出；
- PyInstaller 打包资源。

## 多语言

语言文件位于：

```text
src/locales/
```

新增语言文件后，程序会按文件名自动加入语言下拉菜单。语言显示名在 `src/i18n.py` 中固定，不随当前 UI 语言变化。
