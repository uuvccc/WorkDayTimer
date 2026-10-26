# AGENTS.md

## 项目概览

MiniTools（WorkDayTimer）— Windows 桌面宠物形态的工作时间追踪与提醒应用。PyQt5 无边框置顶窗口，系统托盘集成，支持灵活/固定工时模式、自定义倒计时、自动更新、全局快捷键切换 QQ 窗口。仅支持 Windows。

## 技术栈

- Python 3.10+（CI 使用 3.10，`python_requires=">=3.6"`）
- PyQt5 >= 5.15.0（GUI）
- keyboard / mouse / Pillow / requests / pywin32（**已移除 numpy**，图片透明化为纯 Python 实现）
- Nuitka（standalone 打包）、flake8（lint）、unittest（测试）
- GitHub Actions（CI/CD，runs-on: windows-latest）

## 架构导航

```
main.py                          # 入口，调用 app.application.main()
app/application.py               # MiniToolsApplication — 创建 QApplication + MainWindow
app/main_window.py               # MainWindow(QWidget) — 核心协调者，串联所有服务与 UI
app/config/constants.py          # 路径常量 + 默认配置（get_base_dir 处理路径解析）
app/config/manager.py            # ConfigManager — JSON 配置读写，模块级单例 config_manager
app/services/                    # 各服务均为「类 + 模块级单例」模式
  time_service.py                #   工时计算、start_time.txt 读写
  system_service.py              #   注册表开机自启、QQ 窗口切换(win32gui)、关机
  update_service.py              #   GitHub 检查更新 + 代理镜像回退下载 + updater.bat
  keyboard_service.py            #   全局 Enter 键监听
  feedback_service.py            #   全局键盘/鼠标 Hook（宠物按键/鼠标反馈事件源）
app/ui/
  tray_menu.py                   # 系统托盘菜单
  dialogs/                       # 各对话框（均为 QWidget/QDialog 子类）
app/utils/
  logger.py                      # 日志（get_project_root 处理路径解析，输出到 logs/app.log）
  version.py                     # 语义版本比较
```

**关键模式**：服务层通过 `time_service = TimeService()` 在模块底部创建单例，其他模块直接 `from app.services import time_service` 使用。`config_manager` 同理。修改服务接口时注意所有调用方。

## 路径解析（重要）

**仅发布 exe 版本**（Nuitka standalone），脚本模式已废弃；但开发/测试仍从源码运行，
路径定位逻辑因此保留了 frozen 判断，分布在两处：
- `app/config/constants.py` → `get_base_dir()`
- `app/utils/logger.py` → `get_project_root()`

两者逻辑相同：`getattr(sys, 'frozen', False)` 区分「exe 运行（exe 所在目录）/ 源码运行（项目根）」。
修改路径逻辑时必须同步两处。不要删除 frozen 判断，否则测试运行时配置/日志会写进 Python 安装目录。

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

# 打包（构建参数统一在 build.py，勿用命令行参数另行打包）
python build.py
```

## 版本方案

- 人工版本定义在 `app/__init__.py` 的 `__version__`（项目无 setup.py / pyproject.toml，读取方式：`python -c "from app import __version__; print(__version__)"`）
- CI 自动发布时追加 commit count：`{__version__}.{commit_count}`（如 `1.0.0.142`）
- 版本比较使用 `app/utils/version.py` 的 `is_newer_version()`

## 配置文件

- 统一配置：`settings.json`（JSON 格式，由 ConfigManager 读写）
- 运行时数据：`start_time.txt`（追加写入每日启动时间）
- 旧配置（`flexible_mode.txt`、`reminder_settings.txt`）已被废弃，ConfigManager 启动时自动迁移到 settings.json 后删除

## 更新机制

- 检查更新：直连 `api.github.com`（不走代理），仓库 `uuvccc/WorkDayTimer`
- 增量更新（默认）：下载 `MiniTools.manifest.json` → 比对本地文件的 size/sha256 → 只下载有差异的逐文件 `.gz` 资产 → 解压并校验
- 全量回退：manifest 拉取失败、任一文件下载/校验失败、或没有文件差异时，自动改为下载完整 `MiniTools.zip`
- 下载加速：先直连 GitHub，失败后依次尝试 `GITHUB_PROXY_MIRRORS` 列表中的镜像
- 安全校验：逐文件 sha256 + 大小校验；全量包额外校验 zip 头 PK 魔数（防止代理返回 HTML 错误页）
- 安装：生成 `updater.bat`，请求管理员权限 → taskkill → robocopy 复制暂存目录（增量时只含变化文件）→ 重启

## 打包与发布约定（2026-10）

- `build.py` 是唯一构建入口，CI 与本地统一 `python build.py`，不要在命令行另加打包参数
- 构建产物三件套：`dist/MiniTools.zip`（全量包）+ `dist/MiniTools.manifest.json`（增量清单）+ `dist/assets/*.gz`（逐文件增量资产）
- 资产命名规则：树内路径的 `/` 替换为 `__` 再追加 `.gz`（GitHub release 资产名不允许含 `/`）；manifest 的 `asset` 字段即实际资产名，客户端只用该字段构造下载 URL
- 发布流程：`gh release create --draft` → 上传全部资产 → `gh release edit --draft=false`，保证 `releases/latest` 切换时资产已齐备
- 构建工具版本区间固定 `nuitka>=2.4,<3`、`flake8>=7.0,<8`，两个 workflow 保持一致
- CI 里写 `$GITHUB_OUTPUT` 的步骤必须带 `shell: pwsh`（PS 5.1 的 `Out-File -Encoding utf8` 会写 BOM，导致 output 解析失败）

## 禁止事项

- **禁止** 假设路径 — 所有文件路径必须通过 `constants.py` 的常量获取，不能硬编码相对路径
- **禁止** 在服务单例模块中执行有副作用的顶层代码（除创建单例实例外）
- **禁止** 修改 `get_base_dir()` / `get_project_root()` 逻辑时只改一处
- **禁止** 使用 `print()` 输出日志 — 必须使用 `from app.utils.logger import logger`

## 注意事项

- 应用启动时会 `os.chdir()` 到 exe 所在目录（防止开机自启时 CWD 为 System32）
- Windows AppUserModelID 设为 `"MiniTools"`，确保任务栏图标正确
- 开机自启注册表项：新旧名称分别为 `"MiniTools"` 和 `"WorkDayTimer"`，设置时会清理旧名称
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
| [ascii_animations/README.md](ascii_animations/README.md) | 外部 ASCII 动画导入说明（格式/验证/排查） | 用户导入或自定义动画时 |
