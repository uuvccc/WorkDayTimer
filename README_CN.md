# MiniTools

一个用于追踪工作时间并提供提醒功能的桌面实用工具应用。

## 功能特点

- 自动工作时间追踪
- 签到和签退提醒
- 每日工作日志提醒
- 系统托盘集成
- 可自定义桌面宠物显示
- 支持灵活/固定时间模式
- 自定义计时器功能
- 提醒设置配置
- 自动更新功能
- 开机自启选项

## 系统要求

- Python 3.6 或更高版本
- PyQt5 >= 5.15.0
- 其他依赖项请参见 requirements.txt

## Python环境管理

为了避免Python环境冲突，建议使用虚拟环境。以下是两种常用的环境管理方法：

### 使用venv（Python内置）

1. 创建虚拟环境：
```bash
python -m venv .venv
```

2. 激活虚拟环境：
- Windows:
```bash
.venv\Scripts\activate
```
- Linux/macOS:
```bash
source .venv/bin/activate
```

3. 退出虚拟环境：
```bash
deactivate
```

### 使用Conda

1. 创建新环境：
```bash
conda create -n minitools python=3.8
```

2. 激活环境：
```bash
conda activate minitools
```

3. 退出环境：
```bash
conda deactivate
```

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/uuvccc/WorkDayTimer.git
cd WorkDayTimer
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

有两种运行应用程序的方式：

### 方式1：运行Python脚本

```bash
python main.py
```

### 方式2：运行可执行文件

你也可以直接运行预编译的可执行文件：

1. 从releases页面下载最新版本
2. 解压zip文件
3. 运行 `MiniTools.exe`

启动应用程序后：

1. 计时器将以小桌面宠物的形式出现在屏幕右上角
2. 系统托盘图标提供快速访问：
   - 打开主窗口
   - 切换灵活模式
   - 设置自定义计时器
   - 打开设置对话框
   - 更新应用程序
   - 切换开机自启
   - 退出应用程序
3. 自动提醒功能包括：
   - 签到时间
   - 工作日志提交
   - 签退时间
   - 系统关机（在固定时间模式下）

## 配置

应用程序使用配置文件来管理提醒设置。你可以通过系统托盘菜单访问设置对话框来：
- 启用/禁用签到提醒
- 启用/禁用工作日志提醒
- 启用/禁用签退提醒

## 项目结构

```
WorkDayTimer/
├── main.py                    # 入口文件
├── app/
│   ├── __init__.py
│   ├── application.py         # 应用生命周期管理
│   ├── main_window.py         # 主窗口组件
│   ├── config/
│   │   ├── constants.py       # 配置常量
│   │   └── manager.py         # 配置管理类
│   ├── services/
│   │   ├── time_service.py    # 时间计算服务
│   │   ├── system_service.py  # 系统操作（开机自启、关机、QQ窗口切换）
│   │   ├── update_service.py  # 应用更新服务
│   │   └── keyboard_service.py# 键盘钩子服务
│   ├── ui/
│   │   ├── tray_menu.py       # 系统托盘菜单
│   │   └── dialogs/
│   │       ├── settings_dialog.py      # 设置对话框
│   │       ├── custom_timer_dialog.py  # 自定义计时器对话框
│   │       └── reminder_dialog.py      # 提醒对话框
│   └── utils/
│       ├── logger.py          # 日志工具
│       └── version.py         # 版本比较工具
├── tests/                     # 单元测试
├── images/                    # 计时器图片
├── requirements.txt           # 依赖项
├── setup.py                   # 包配置
└── workday_timer.spec         # PyInstaller 配置
```

## 打包

要构建可执行文件：

```bash
python workday_timer.spec
```

或者直接使用PyInstaller：

```bash
pyinstaller --onefile --windowed --name MiniTools main.py
```

## 贡献

欢迎贡献！请随时提交Pull Request。

## 许可证

本项目采用MIT许可证 - 详情请参见LICENSE文件