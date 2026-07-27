# WorkDayTimer 重构计划

## 一、现状分析

**当前问题：**
- 单文件 `workday_timer.py` 超过 850 行，职责混杂
- 全局可变状态（`isFLEXIBLE`、`reminder_settings`）跨模块引用
- `QTimer` 生命周期管理存在历史 bug
- `keyboard` 钩子 + `win32` API 与 UI 线程耦合
- 配置逻辑混合在 `config.py` 中，缺少统一管理
- 缺少异常处理和日志规范

## 二、目标架构

```
workday_timer/
├── main.py                    # 入口文件
├── app/
│   ├── __init__.py
│   ├── application.py         # 应用入口类
│   ├── main_window.py         # 主窗口
│   ├── config/
│   │   ├── __init__.py
│   │   ├── constants.py       # 配置常量
│   │   └── manager.py         # 配置管理类
│   ├── services/
│   │   ├── __init__.py
│   │   ├── time_service.py    # 时间计算服务
│   │   ├── system_service.py  # 系统服务（键盘钩子、win32、开机自启）
│   │   └── update_service.py  # 更新服务
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── dialogs/           # 对话框
│   │   │   ├── __init__.py
│   │   │   ├── settings_dialog.py
│   │   │   ├── custom_timer_dialog.py
│   │   │   └── reminder_dialog.py
│   │   └── tray_menu.py       # 系统托盘菜单
│   ├── resources/             # 资源文件
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # 日志工具
│       └── version.py         # 版本比较工具
├── tests/                     # 测试用例
├── requirements.txt
└── setup.py
```

## 三、分阶段重构计划

### Phase 1: 基础架构搭建（低风险）

**目标：** 建立项目结构和基础工具，不影响现有功能

**任务：**
1. 创建目录结构（`app/`, `app/config/`, `app/services/`, `app/ui/`, `app/utils/`）
2. 抽取日志工具 `app/utils/logger.py`
3. 抽取版本比较工具 `app/utils/version.py`
4. 重构配置模块：
   - `app/config/constants.py` - 配置常量
   - `app/config/manager.py` - 配置管理类（替代全局变量）
5. 更新 `config.py` 为兼容层，保持向后兼容

**验证标准：**
- 所有模块可导入
- 配置读写功能正常
- 日志输出正常

### Phase 2: 业务逻辑抽取（中等风险）

**目标：** 将无 Qt 依赖的纯逻辑抽取为独立服务

**任务：**
1. 创建时间计算服务 `app/services/time_service.py`
   - 抽取 `get_last_start_time()`、`write_start_time()`
   - 实现工作时间计算逻辑
2. 创建系统服务 `app/services/system_service.py`
   - 抽取 `is_run_on_startup()`、`toggle_run_on_startup()`
   - 抽取 `toggle_qq_window()`（win32 API）
   - 抽取键盘钩子逻辑
3. 创建更新服务 `app/services/update_service.py`
   - 抽取 `check_for_updates()`、`update_application()`
   - 抽取 `_is_newer_version()`

**验证标准：**
- 各服务模块独立运行测试通过
- 配置管理类替代全局变量后功能正常

### Phase 3: UI 层重构（中等风险）

**目标：** 将 UI 组件拆分为独立模块

**任务：**
1. 创建系统托盘菜单 `app/ui/tray_menu.py`
   - 抽取菜单创建逻辑
   - 保持信号槽连接
2. 创建对话框模块：
   - `app/ui/dialogs/settings_dialog.py`
   - `app/ui/dialogs/custom_timer_dialog.py`
   - `app/ui/dialogs/reminder_dialog.py`（整合所有提醒对话框）
3. 重构主窗口 `app/main_window.py`
   - 简化主窗口逻辑
   - 集成各服务模块
4. 创建应用入口类 `app/application.py`
   - 统一管理应用生命周期

**验证标准：**
- 系统托盘菜单功能正常
- 所有对话框功能正常
- 主窗口显示和交互正常

### Phase 4: 主文件整合（高风险）

**目标：** 整合所有模块，替换原有单文件

**任务：**
1. 创建新的 `main.py` 入口文件
2. 删除或归档旧的 `workday_timer.py`
3. 修复 `QTimer` 生命周期管理 bug（reminder_timer2 的 setSingleShot）
4. 添加全局异常处理
5. 优化资源管理（使用 `.qrc` 文件）

**验证标准：**
- 应用启动正常
- 所有提醒功能正常
- 设置保存和加载正常
- 自动更新功能正常

### Phase 5: 测试和质量保证

**目标：** 完善测试和代码质量

**任务：**
1. 添加单元测试用例
2. 使用 `pylint`/`flake8` 检查代码质量
3. 添加 `mypy` 类型检查
4. 优化打包配置

**验证标准：**
- 测试覆盖率达到 80%
- 代码质量检查通过
- 打包后的可执行文件正常运行

## 四、关键风险点

| 风险点 | 风险等级 | 应对措施 |
|--------|----------|----------|
| 全局变量替换 | 高 | 采用配置管理类，逐步替换 |
| QTimer 生命周期 | 高 | 明确父子关系，统一管理 |
| 键盘钩子线程安全 | 高 | 隔离为独立服务，使用信号槽通信 |
| UI 组件拆分 | 中 | 先抽离无状态组件，再处理有状态组件 |
| 功能回归 | 中 | 每个阶段进行功能验证 |

## 五、进度预估

| 阶段 | 预估时间 | 可验证产出 |
|------|----------|------------|
| Phase 1 | 1-2 天 | 目录结构、配置管理、日志工具 |
| Phase 2 | 2-3 天 | 时间服务、系统服务、更新服务 |
| Phase 3 | 2-3 天 | 托盘菜单、对话框、主窗口重构 |
| Phase 4 | 1-2 天 | 主入口整合、bug 修复 |
| Phase 5 | 1-2 天 | 测试、代码检查、打包优化 |
| **总计** | **7-12 天** | 完整重构后的项目 |

## 六、执行原则

1. **渐进式重构**：每个阶段只修改最小范围，确保功能正常
2. **向后兼容**：重构过程中保持原有 API 兼容
3. **测试驱动**：每个模块都有对应的测试用例
4. **代码审查**：重要修改进行代码审查
5. **文档更新**：同步更新项目文档
