# PROGRESS.md

## 当前状态

**最新完成**：AI 规则体系搭建（2026-08）

---

## 变更日志

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
