# ARCHITECTURE.md

## 系统架构概览

```
┌─────────────────────────────────────────────────┐
│                   main.py                        │
│                      │                           │
│            MiniToolsApplication                  │
│           (application.py)                       │
│            ┌─────┴─────┐                         │
│            │           │                         │
│       MainWindow    TrayMenu                     │
│    (main_window.py) (tray_menu.py)               │
│         │                                        │
│    ┌────┼────┬─────────┬──────────┐              │
│    │    │    │         │          │              │
│  Time  Sys  Update  Keyboard   UI Dialogs        │
│  Service Service Service Service (dialogs/)      │
│    │    │    │         │          │              │
│    └────┴────┴─────────┴──────────┘              │
│                      │                           │
│              ConfigManager                       │
│           (config/manager.py)                    │
│                      │                           │
│              constants.py                        │
│           (路径常量 + 默认配置)                    │
└─────────────────────────────────────────────────┘
```

## 模块职责

| 模块 | 文件 | 职责 | 依赖方向 |
|------|------|------|---------|
| 入口 | `main.py` | 启动应用 | → application |
| 应用生命周期 | `application.py` | 创建 QApplication、异常处理、CWD 修正 | → main_window, config, utils |
| 主窗口 | `main_window.py` | 核心协调者：串联服务与 UI、定时器管理 | → config, services, ui, utils |
| 路径常量 | `config/constants.py` | 双模式路径计算、默认配置 | 无外部依赖 |
| 配置管理 | `config/manager.py` | JSON 配置读写、旧配置迁移 | → constants, utils |
| 时间服务 | `services/time_service.py` | 工时计算、启动时间持久化 | → config, utils |
| 系统服务 | `services/system_service.py` | 注册表自启、QQ 窗口切换、关机 | → utils |
| 更新服务 | `services/update_service.py` | GitHub 检查更新、代理下载、updater.bat | → utils |
| 键盘服务 | `services/keyboard_service.py` | 全局 Enter 键监听 | → utils |
| 托盘菜单 | `ui/tray_menu.py` | 系统托盘图标与右键菜单 | → utils |
| 对话框 | `ui/dialogs/*.py` | 各类弹窗 UI | → utils |
| 日志 | `utils/logger.py` | 双模式日志（文件 + 控制台） | 无外部依赖 |
| 版本 | `utils/version.py` | 语义版本比较 | 无外部依赖 |

## 关键设计模式

### 服务层单例

所有服务采用「类 + 模块级实例」模式：

```python
# services/time_service.py
class TimeService:
    ...
time_service = TimeService()  # 模块底部创建单例
```

其他模块通过 `from app.services import time_service` 直接引用。修改服务接口时必须检查所有调用方。

### 双模式路径

`constants.py` 的 `get_base_dir()` 和 `logger.py` 的 `get_project_root()` 使用相同逻辑：
- exe 模式：`os.path.dirname(sys.executable)`
- 脚本模式：`__file__` 上两级目录
- 判断条件：`getattr(sys, 'frozen', False)`

### 配置持久化

- 运行时配置统一存储在 `settings.json`（JSON 格式）
- ConfigManager 启动时自动从旧格式（txt 文件）迁移
- 配置变更通过 property setter 自动持久化
- 批量变更使用 `apply_changes()` 避免多次写盘

## 依赖约束

- `utils/` 不依赖 `services/`、`ui/`、`config/manager.py`
- `config/constants.py` 不依赖任何其他模块
- `services/` 之间不互相依赖
- `ui/` 可以依赖 `services/` 和 `config/`，但不反向
- `main_window.py` 是唯一的"胶水层"，负责串联所有模块
