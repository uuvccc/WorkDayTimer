# AGENTS.md

## 项目概览

MiniTools（WorkDayTimer）— Windows 桌面宠物形态的工作时间追踪与提醒应用。PyQt5 无边框置顶窗口，系统托盘集成，支持灵活/固定工时模式、自定义倒计时、自动更新、全局快捷键切换 QQ 窗口。仅支持 Windows。

## 技术栈

- Python 3.10+（CI 使用 3.10，`python_requires=">=3.6"`）
- PyQt5 >= 5.15.0（GUI）
- keyboard / Pillow / requests / numpy / pywin32
- PyInstaller（打包）、flake8（lint）、unittest（测试）
- GitHub Actions（CI/CD，runs-on: windows-latest）

## 架构导航

```
main.py                          # 入口，调用 app.application.main()
app/application.py               # MiniToolsApplication — 创建 QApplication + MainWindow
app/main_window.py               # MainWindow(QWidget) — 核心协调者，串联所有服务与 UI
app/config/constants.py          # 路径常量 + 默认配置（get_base_dir 处理双模式路径）
app/config/manager.py            # ConfigManager — JSON 配置读写，模块级单例 config_manager
app/services/                    # 各服务均为「类 + 模块级单例」模式
  time_service.py                #   工时计算、start_time.txt 读写
  system_service.py              #   注册表开机自启、QQ 窗口切换(win32gui)、关机
  update_service.py              #   GitHub 检查更新 + 代理镜像回退下载 + updater.bat
  keyboard_service.py            #   全局 Enter 键监听
app/ui/
  tray_menu.py                   # 系统托盘菜单
  dialogs/                       # 各对话框（均为 QWidget/QDialog 子类）
app/utils/
  logger.py                      # 日志（get_project_root 处理双模式路径，输出到 logs/app.log）
  version.py                     # 语义版本比较
```

**关键模式**：服务层通过 `time_service = TimeService()` 在模块底部创建单例，其他模块直接 `from app.services import time_service` 使用。`config_manager` 同理。修改服务接口时注意所有调用方。

## 双模式路径（重要）

项目同时支持 **exe 打包模式** 和 **Python 脚本模式**，路径定位逻辑分布在两处：
- `app/config/constants.py` → `get_base_dir()`
- `app/utils/logger.py` → `get_project_root()`

两者逻辑相同：`getattr(sys, 'frozen', False)` 判断是否 exe 模式。修改路径逻辑时必须同步两处。

## 开发命令

```powershell
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 测试（必须从项目根目录执行）
python -m unittest discover tests -v

# Lint
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 打包
pyinstaller --onefile --windowed --name MiniTools main.py
```

## 版本方案

- 人工版本定义在 `app/__init__.py` 的 `__version__`
- CI 自动发布时追加 commit count：`{__version__}.{commit_count}`（如 `1.0.0.142`）
- 版本比较使用 `app/utils/version.py` 的 `is_newer_version()`
- **禁止 `import setup`** — setup.py 顶层调用 `setup()` 会触发 `sys.exit(1)`，导致进程终止

## 配置文件

- 统一配置：`settings.json`（JSON 格式，由 ConfigManager 读写）
- 运行时数据：`start_time.txt`（追加写入每日启动时间）
- 旧配置（`flexible_mode.txt`、`reminder_settings.txt`）已被废弃，ConfigManager 启动时自动迁移到 settings.json 后删除

## 更新机制

- 检查更新：直连 `api.github.com`（不走代理），仓库 `uuvccc/WorkDayTimer`
- 下载更新：先直连 GitHub，失败后依次尝试 `GITHUB_PROXY_MIRRORS` 列表中的镜像
- 安全校验：文件大小校验 + PE 头 MZ 魔数校验（防止代理返回 HTML 错误页）
- exe 模式更新：生成 `updater.bat`，请求管理员权限 → taskkill → 替换 exe → 重启
- 脚本模式更新：直接下载到当前目录

## 禁止事项

- **禁止** `import setup` 或 `from setup import ...`（会导致进程退出）
- **禁止** 假设路径 — 所有文件路径必须通过 `constants.py` 的常量获取，不能硬编码相对路径
- **禁止** 在服务单例模块中执行有副作用的顶层代码（除创建单例实例外）
- **禁止** 修改 `get_base_dir()` / `get_project_root()` 逻辑时只改一处
- **禁止** 使用 `print()` 输出日志 — 必须使用 `from app.utils.logger import logger`

## 注意事项

- 应用启动时会 `os.chdir()` 到 exe/脚本所在目录（防止开机自启时 CWD 为 System32）
- Windows AppUserModelID 设为 `"MiniTools"`，确保任务栏图标正确
- 开机自启注册表项：新旧名称分别为 `"MiniTools"` 和 `"WorkDayTimer"`，设置时会清理旧名称
- 开机自启脚本模式使用 `pythonw.exe`（无控制台窗口）
- QQ 窗口通过 `win32gui.EnumWindows` 匹配标题含 `"QQ..exe"` 的窗口
- 主窗口：无边框 + 置顶 + 半透明背景，初始位置动态计算为屏幕右上角

## 文档索引

| 文档 | 说明 | 何时阅读 |
|------|------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构、模块职责、依赖约束 | 修改模块边界或新增模块前 |
| [PRODUCT_SENSE.md](PRODUCT_SENSE.md) | 产品定位、目标用户、功能边界 | 新增功能或评估需求前 |
| [PLANS.md](PLANS.md) | 当前开发计划与待办 | 了解项目方向或领取任务前 |
| [PROGRESS.md](PROGRESS.md) | 历史变更记录 | 了解项目演进或排查问题时 |
| [docs/design-docs/](docs/design-docs/) | 功能设计文档 | 实现新功能前 |
| [docs/exec-plans/](docs/exec-plans/) | 执行计划（active/completed） | 执行具体任务前 |
