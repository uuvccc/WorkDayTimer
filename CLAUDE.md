# WorkDayTimer 项目说明

## 项目概述

WorkDayTimer（MiniTools）是一个用于追踪工作时间并提供提醒功能的桌面计时器应用。它以桌面宠物形式显示，支持灵活/固定时间模式，并集成了系统托盘功能。

## 技术栈

- **语言**: Python 3.6+
- **GUI框架**: PyQt5
- **键盘监听**: keyboard
- **图像处理**: Pillow
- **网络请求**: requests
- **数值计算**: numpy
- **Windows API**: pywin32

## 文件结构

```
WorkDayTimer/
├── app/
│   ├── __init__.py
│   ├── application.py      # 应用入口类（MiniToolsApplication）
│   ├── main_window.py      # 主窗口类（MainWindow）
│   ├── config/
│   │   ├── __init__.py
│   │   ├── constants.py    # 静态配置常量
│   │   └── manager.py      # 配置管理器（ConfigManager）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── keyboard_service.py  # 键盘监听服务
│   │   ├── system_service.py    # 系统操作服务（开机自启、关机、QQ切换）
│   │   ├── time_service.py      # 时间计算服务
│   │   └── update_service.py    # 自动更新服务
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── tray_menu.py     # 系统托盘菜单
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       ├── custom_timer_dialog.py  # 自定义计时器对话框
│   │       ├── reminder_dialog.py      # 提醒对话框
│   │       └── settings_dialog.py      # 设置对话框（提醒开关、开机自启开关）
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # 日志工具
│       └── version.py       # 版本比较工具
├── images/
│   ├── icon.ico             # 应用图标（ICO格式）
│   ├── icon.png             # 应用图标（PNG格式）
│   ├── icon.svg             # 应用图标（SVG格式）
│   ├── timer1.png           # 默认计时器图片
│   ├── avatars/             # 头像图片目录
│   ├── avatars2/            # 头像图片目录2
│   └── timers/              # 计时器动画图片目录
├── tests/
│   ├── __init__.py
│   ├── test_config_manager.py
│   ├── test_time_service.py
│   └── test_version.py
├── .github/workflows/
│   ├── auto-release.yml     # 自动发布工作流
│   └── python-app.yml       # Python应用CI工作流
├── main.py                  # 应用入口
├── requirements.txt         # 依赖列表
├── setup.py                 # 打包配置
├── convert_icon.py          # 图标转换工具（SVG转PNG/ICO）
├── start_time.txt           # 开始时间记录（运行时生成）
├── flexible_mode.txt        # 灵活模式状态（运行时生成）
├── reminder_settings.txt    # 提醒设置（运行时生成）
└── app.log                  # 日志文件（运行时生成）
```

## 核心功能

### 1. 工作时间追踪
- 自动记录每日首次启动时间
- 支持固定模式（9:00 AM 开始）和灵活模式
- 8.5小时工作时长倒计时

### 2. 提醒功能
- **签到提醒**: 每日首次启动时弹出（可独立开关）
- **工作日志提醒**: 工作7.5小时后提醒（可独立开关）
- **签退提醒**: 工作8.5小时后提醒（可独立开关）
- **系统关机**: 固定模式下可一键关机

### 3. 设置对话框
- 独立开关：签到提醒、工作日志提醒、签退提醒
- 开机自启开关

### 4. 自定义计时器
- 支持设置任意时长的自定义倒计时
- 提供快速选择按钮（1-30分钟、40、60、90、120、180、240分钟）

### 5. 系统托盘集成
- 显示应用状态图标
- 右键菜单：打开/退出、切换灵活模式、自定义计时器、设置、更新应用、开机自启

### 6. 自动更新
- 检查 GitHub 最新版本
- 自动下载并替换可执行文件

### 7. 快捷键支持
- 监听全局 Enter 键，用于切换 QQ 窗口显示/隐藏

### 8. 窗口自适应
- 初始位置自动定位到屏幕右上角（动态计算）
- 适配不同屏幕分辨率

## 核心类

### MiniToolsApplication (application.py)

应用入口类，负责初始化和运行应用。

| 方法 | 功能 |
|------|------|
| `run()` | 运行应用主循环 |
| `_setup_exception_handler()` | 设置全局异常处理 |

### MainWindow (main_window.py)

主窗口类，继承自 QWidget，包含以下关键方法：

| 方法 | 功能 |
|------|------|
| `__init__(app)` | 初始化主窗口 |
| `_setup_ui()` | 初始化界面，动态计算右上角位置 |
| `update_timer_display()` | 更新计时器显示，随机切换图片 |
| `show_checkin_reminder()` | 显示签到提醒对话框 |
| `show_checkout_reminder()` | 显示签退提醒对话框 |
| `show_job_record_warning()` | 显示工作日志提醒对话框 |
| `show_custom_timer_dialog()` | 显示自定义计时器对话框 |
| `show_settings_dialog()` | 显示设置对话框 |
| `toggle_flexible_mode(checked)` | 切换灵活/固定模式 |
| `toggle_run_on_startup(checked)` | 切换开机自启设置 |
| `update_application()` | 下载并安装更新 |
| `toggle_qq_window()` | 切换 QQ 窗口显示/隐藏 |

### 服务类

#### TimeService (time_service.py)

| 方法 | 功能 |
|------|------|
| `get_last_start_time()` | 获取上次启动时间 |
| `write_start_time(start_time)` | 写入启动时间 |
| `is_first_start_of_day()` | 判断是否为当天首次启动 |
| `calculate_work_end_time(start_time, is_flexible)` | 计算工作结束时间 |
| `calculate_remaining_seconds(target_time)` | 计算剩余秒数 |
| `get_work_progress(start_time, is_flexible)` | 获取工作进度百分比 |

#### SystemService (system_service.py)

| 方法 | 功能 |
|------|------|
| `is_run_on_startup()` | 检查是否已设置开机自启 |
| `toggle_run_on_startup(is_enabled)` | 设置/取消开机自启 |
| `toggle_qq_window()` | 切换 QQ 窗口显示/隐藏 |
| `shutdown_computer()` | 关机 |
| `is_running_as_exe()` | 检查是否以可执行文件运行 |

#### UpdateService (update_service.py)

| 方法 | 功能 |
|------|------|
| `get_current_version()` | 获取当前版本 |
| `check_for_updates()` | 检查更新 |
| `download_update(progress_callback)` | 下载更新 |
| `prepare_updater_script(temp_exe_path, local_exe_path)` | 准备更新脚本 |
| `run_updater(updater_script)` | 运行更新脚本 |

#### KeyboardService (keyboard_service.py)

| 方法 | 功能 |
|------|------|
| `set_enter_key_callback(callback)` | 设置 Enter 键回调 |
| `start_listening()` | 开始监听键盘事件 |
| `stop_listening()` | 停止监听 |

### UI 类

#### TrayMenu (tray_menu.py)

系统托盘菜单类。

| 方法 | 功能 |
|------|------|
| `set_flexible_mode(is_flexible)` | 更新灵活模式菜单状态 |
| `set_run_on_startup(is_enabled)` | 更新开机自启菜单状态 |
| `show_message(title, message, icon, duration)` | 显示托盘消息 |

#### SettingsDialog (settings_dialog.py)

设置对话框，包含提醒开关和开机自启开关。

#### CustomTimerDialog (custom_timer_dialog.py)

自定义计时器对话框。

| 方法 | 功能 |
|------|------|
| `get_minutes()` | 获取用户输入的分钟数 |

#### ReminderDialog (reminder_dialog.py)

提醒对话框，提供静态方法：

| 方法 | 功能 |
|------|------|
| `show_checkin(parent)` | 显示签到提醒 |
| `show_job_record(parent)` | 显示工作日志提醒 |
| `show_checkout(parent, is_flexible, shutdown_callback)` | 显示签退提醒 |
| `show_custom_timer(parent)` | 显示自定义计时器完成提醒 |
| `show_update_available(parent)` | 显示更新可用提示 |

### 配置管理

#### ConfigManager (config/manager.py)

配置管理器，提供以下属性和方法：

| 属性/方法 | 功能 |
|-----------|------|
| `is_flexible` | 灵活模式状态（可读写） |
| `reminder_settings` | 获取所有提醒设置 |
| `get_reminder_setting(key)` | 获取指定提醒设置 |
| `set_reminder_setting(key, value)` | 设置提醒设置 |
| `toggle_reminder_setting(key)` | 切换提醒设置状态 |

## 配置项

### constants.py 中的关键配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `START_TIME_FILE` | str | start_time.txt | 开始时间记录文件路径 |
| `FLEXIBLE_MODE_FILE` | str | flexible_mode.txt | 灵活模式状态文件路径 |
| `REMINDER_SETTINGS_FILE` | str | reminder_settings.txt | 提醒设置文件路径 |
| `WINDOW_SIZE_WIDTH` | int | 200 | 主窗口宽度 |
| `WINDOW_SIZE_HEIGHT` | int | 200 | 主窗口高度 |
| `DIALOG_POSITION_X` | int | 700 | 对话框位置X |
| `DIALOG_POSITION_Y` | int | 500 | 对话框位置Y |
| `DIALOG_SIZE_WIDTH` | int | 750 | 对话框宽度 |
| `DIALOG_SIZE_HEIGHT` | int | 550 | 对话框高度 |
| `JOB_DIALOG_SIZE_WIDTH` | int | 900 | 工作日志对话框宽度 |
| `JOB_DIALOG_SIZE_HEIGHT` | int | 700 | 工作日志对话框高度 |

### 默认提醒设置

| 设置项 | 默认值 | 说明 |
|--------|--------|------|
| `checkin_reminder` | True | 签到提醒 |
| `job_record_reminder` | True | 工作日志提醒 |
| `checkout_reminder` | True | 签退提醒 |

## 运行方式

### 开发模式

```bash
pip install -r requirements.txt
python main.py
```

### 可执行文件

直接运行 `WorkDayTimer.exe`（需从 GitHub Releases 下载）

## 打包说明

项目使用 PyInstaller 打包，打包命令通常为：

```bash
pyinstaller --onefile --windowed --icon=images/icon.ico main.py
```

## 日志系统

应用会在应用目录下的 `logs/` 文件夹中生成 `app.log` 文件，记录 DEBUG 级别及以上的日志。

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

## 注意事项

1. **系统兼容性**: 应用使用了 `pywin32` 和 Windows 特定 API，仅支持 Windows 系统
2. **权限要求**: 自动更新和开机自启功能需要管理员权限
3. **键盘权限**: 全局键盘监听需要管理员权限
4. **图片资源**: 确保 `images/` 目录下有正确的图片文件
5. **窗口位置**: 主窗口初始位置自动计算为屏幕右上角，无需手动配置