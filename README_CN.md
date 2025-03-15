# WorkdayTimer

一个用于追踪工作时间并提供提醒功能的桌面计时器应用。

## 功能特点

- 自动工作时间追踪
- 签到和签退提醒
- 每日工作日志提醒
- 系统托盘集成
- 可自定义桌面宠物显示
- 支持灵活/固定时间模式

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
conda create -n workdaytimer python=3.8
```

2. 激活环境：
```bash
conda activate workdaytimer
```

3. 退出环境：
```bash
conda deactivate
```

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/WorkDayTimer.git
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
python workday_timer.py
```

### 方式2：运行可执行文件

你也可以直接运行预编译的可执行文件：

1. 从releases页面下载最新版本
2. 解压zip文件
3. 运行 `workday_timer.exe`

启动应用程序后：

1. 计时器将以小桌面宠物的形式出现在屏幕右上角
2. 系统托盘图标提供快速访问以打开/退出应用程序
3. 自动提醒功能包括：
   - 签到时间
   - 工作日志提交
   - 签退时间
   - 系统关机（在固定时间模式下）

## 配置

- `isFLEXIBLE`：设置为 `True` 表示灵活工作时间，`False` 表示固定9:00 AM开始时间
- 可以在代码中自定义图片路径以更改桌面宠物外观
- 可以在初始化参数中调整窗口位置和大小

## 贡献

欢迎贡献！请随时提交Pull Request。

## 许可证

本项目采用MIT许可证 - 详情请参见LICENSE文件