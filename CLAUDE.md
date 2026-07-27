# WorkDayTimer 项目说明

## 项目概述

WorkDayTimer 是一个用于追踪工作时间并提供提醒功能的桌面计时器应用。它以桌面宠物形式显示，支持灵活/固定时间模式，并集成了系统托盘功能。

## 技术栈

- **语言**: Python 3.6+
- **GUI框架**: PyQt5
- **键盘监听**: keyboard
- **图像处理**: Pillow、Wand
- **网络请求**: requests
- **数值计算**: numpy
- **Windows API**: pywin32

## 文件结构

```
WorkDayTimer/
├── workday_timer.py      # 主应用代码（核心）
├── config.py             # 配置文件
├── convert_icon.py       # 图标转换工具（SVG转PNG/ICO）
├── setup.py              # 打包配置
├── requirements.txt      # 依赖列表
├── start_time.txt        # 开始时间记录（运行时生成）
├── flexible_mode.txt     # 灵活模式状态（运行时生成）
├── app.log               # 日志文件（运行时生成）
├── images/
│   ├── icon.ico          # 应用图标（ICO格式）
│   ├── icon.png          # 应用图标（PNG格式）
│   ├── icon.svg          # 应用图标（SVG格式）
│   ├── timer1.png        # 默认计时器图片
│   ├── avatars/          # 头像图片目录
│   ├── avatars2/         # 头像图片目录2
│   └── timers/           # 计时器动画图片目录
└── .github/workflows/    # GitHub Actions 工作流
    ├── auto-release.yml  # 自动发布工作流
    └── python-app.yml    # Python应用CI工作流
```

## 核心功能

### 1. 工作时间追踪
- 自动记录每日首次启动时间
- 支持固定模式（9:00 AM 开始）和灵活模式
- 8.5小时工作时长倒计时

### 2. 提醒功能
- **签到提醒**: 每日首次启动时弹出
- **工作日志提醒**: 工作7.5小时后提醒
- **签退提醒**: 工作8.5小时后提醒
- **系统关机**: 固定模式下可一键关机

### 3. 自定义计时器
- 支持设置任意时长的自定义倒计时
- 提供快速选择按钮（1-30分钟、40、60、90、120、180、240分钟）

### 4. 系统托盘集成
- 显示应用状态图标
- 右键菜单：打开/退出、切换灵活模式、自定义计时器、更新应用、开机自启

### 5. 自动更新
- 检查 GitHub 最新版本
- 自动下载并替换可执行文件

### 6. 快捷键支持
- 监听全局 Enter 键，用于切换 QQ 窗口显示/隐藏

## 核心类

### WorkdayTimer (QWidget)

主窗口类，继承自 QWidget，包含以下关键方法：

| 方法 | 功能 |
|------|------|
| `__init__()` | 初始化应用，设置计时器、系统托盘、键盘钩子 |
| `init_ui()` | 初始化界面，创建计时器窗口 |
| `update_timer_display()` | 更新计时器显示，随机切换图片 |
| `show_checkin_reminder()` | 显示签到提醒对话框 |
| `show_reminder()` | 显示签退提醒对话框 |
| `show_job_record_warning()` | 显示工作日志提醒对话框 |
| `toggle_flexible_mode()` | 切换灵活/固定模式 |
| `toggle_run_on_startup()` | 切换开机自启设置 |
| `show_custom_timer_dialog()` | 显示自定义计时器对话框 |
| `check_for_updates()` | 检查应用更新 |
| `update_application()` | 下载并安装更新 |
| `toggle_qq_window()` | 切换 QQ 窗口显示/隐藏 |

## 配置项

配置文件 `config.py` 中的关键配置：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `isFLEXIBLE` | bool | False | 灵活模式开关 |
| `START_TIME_FILE` | str | start_time.txt | 开始时间记录文件路径 |
| `FLEXIBLE_MODE_FILE` | str | flexible_mode.txt | 灵活模式状态文件路径 |
| `WINDOW_POSITION_X/Y` | int | 1650/30 | 主窗口位置 |
| `WINDOW_SIZE_WIDTH/HEIGHT` | int | 200/200 | 主窗口大小 |
| `DIALOG_POSITION_X/Y` | int | 700/500 | 对话框位置 |

## 运行方式

### 开发模式

```bash
pip install -r requirements.txt
python workday_timer.py
```

### 可执行文件

直接运行 `WorkDayTimer.exe`（需从 GitHub Releases 下载）

## 打包说明

项目使用 PyInstaller 打包，打包命令通常为：

```bash
pyinstaller --onefile --windowed --icon=images/icon.ico workday_timer.py
```

## 日志系统

应用会在应用目录下生成 `app.log` 文件，记录 DEBUG 级别及以上的日志。

## 开发指南

### 代码规范
- 使用 Python 3.6+ 语法
- 使用 PyQt5 进行 GUI 开发
- 使用 Python 内置 `logging` 模块记录日志
- 注释使用中文和英文混合

### CI/CD
- 使用 GitHub Actions 进行持续集成
- `python-app.yml`: 运行 Python 应用测试
- `auto-release.yml`: 自动发布新版本

### 图标转换
使用 `convert_icon.py` 将 SVG 图标转换为 PNG 和 ICO 格式：

```bash
pip install wand pillow
python convert_icon.py
```

## 已知问题

1. **重复的 `keyPressEvent` 方法**: 在 `workday_timer.py` 中定义了两个 `keyPressEvent` 方法（第206行和第532行），第二个定义会覆盖第一个。

2. **`reminder_timer2` 的 `setSingleShot` 设置错误**: 第101行应该设置 `self.reminder_timer2.setSingleShot(True)`，但实际设置的是 `self.reminder_timer.setSingleShot(True)`，导致 `reminder_timer` 的单触发模式被重复设置，而 `reminder_timer2` 未被正确设置。

3. **GitHub 仓库 URL 不一致**: README.md 中使用的仓库地址是 `wasd845/WorkDayTimer`，而代码中（第555行和第611行）使用的是 `uuvccc/WorkDayTimer`。

## 注意事项

1. **系统兼容性**: 应用使用了 `pywin32` 和 Windows 特定 API，仅支持 Windows 系统
2. **权限要求**: 自动更新和开机自启功能需要管理员权限
3. **键盘权限**: 全局键盘监听需要管理员权限
4. **图片资源**: 确保 `images/` 目录下有正确的图片文件