# PROGRESS.md

## 当前状态

**最新完成**：手动检查更新与「启动时自动检测」开关解耦（2026-09）

---

## 变更日志

### 2026-09 — 手动检查更新不受自动检测开关限制

**问题**：`auto_check_update`（启动时自动检测）关闭后，Settings → About 的手动
「Check for Updates...」按钮也被一并禁用，只能先去 System 页把开关打开才能更新。

**修复**：
- `app/ui/dialogs/settings_dialog.py` — 手动检查不再读取 `auto_check_update`，
  始终可发起一次即时查询；查询在后台线程执行，结果经定时器轮询回 GUI 线程
- 检查到新版本 → 弹确认框，确认后走原有下载/安装流程；已是最新 → 提示无需更新；
  检查失败 → 提示网络问题
- `tests/test_settings_update.py` — 覆盖「自动检测关闭时手动仍可检查」等场景

---

### 2026-09 — 按键/鼠标输入反馈提示

**新增文件**：
- `app/services/feedback_service.py` — 全局键盘/鼠标 Hook → 回调 UI 的服务
- `tests/test_feedback_ascii.py` — 按键名/鼠标键映射、键帽渲染单测

**改进**：
- 全局按下的键（字母/数字/符号/功能键）与鼠标按钮（LMB/RMB/MMB/侧键）实时显示在宠物上方
- 独立浮层：透明无底片、无边框的纯文字提示，融入宠物黑色 ASCII 风格，出现/消失不挤压动画布局
- Hook 线程事件经 `QApplication.postEvent` 安全投递到 GUI 线程
- 配置新增 `show_input_feedback`（默认开启，Settings → Pet 可关闭）
- 依赖新增 `mouse>=0.7.1`（与 `keyboard` 配套的鼠标 Hook 库）

**注意**：显示全部按键会把打字内容（含密码）显示在屏幕上，可随时在设置里关闭。

---

### 2026-08 — AI 规则体系搭建

**新增文件**：
- `AGENTS.md` — AI Agent 入口导航（~100 行）
- `ARCHITECTURE.md` — 系统架构与模块职责
- `PRODUCT_SENSE.md` — 产品定位与功能边界
- `PLANS.md` — 开发计划追踪
- `PROGRESS.md` — 本文件，进度记录
- `docs/exec-plans/` — 执行计划目录
- `docs/design-docs/` — 设计文档目录

**删除文件**：
- `CLAUDE.md` — 已迁移至 `AGENTS.md`

**改进**：
- 从 308 行单文件精简为 102 行 AGENTS.md
- 补全了架构导航、双模式路径、禁止事项等关键规则
- 建立了渐进式披露的文档体系

---

### 2025 — 配置系统重构

**改进**：
- 统一配置到 `settings.json`
- 旧 txt 配置文件自动迁移
- ConfigManager 支持批量更新

---

### 早期版本

- 基础工作时间追踪功能
- 签到/签退/日志提醒
- 系统托盘集成
- 自定义计时器
- 自动更新（GitHub Releases）
- 全局 Enter 键切换 QQ 窗口
- PyInstaller 打包 + CI/CD
