# PROGRESS.md

## 当前状态

**最新完成**：AI 规则体系搭建（2026-08）

---

## 变更日志

### 2026-08 — 桌面宠物重新设计（feature/pet-redesign）

**改进**：
- 新增 `app/ui/pet_widget.py`：混合式宠物组件（顶部头像随状态动效 + 环形进度 + HH:MM:SS 倒计时 + 底部中文状态文案）
- 5 种状态（等待开工 / 工作中 / 快下班 / 已下班 / 自定义倒计时），各有主题色与动效（呼吸 / 弹跳 / 庆祝）
- 修复：倒计时不再依赖签退提醒定时器，签退提醒关闭时仍正常显示；移除每 100ms 重置窗口标志的性能反模式
- 高 DPI 支持（QApplication 创建前启用缩放）
- CI：feature 分支每次 push 发布 prerelease（分支后缀 tag，不冲突、不进入正式更新通道）

**新增文件**：
- `app/ui/pet_widget.py`
- `tests/test_pet_widget.py`

**修改文件**：
- `app/main_window.py`（显示层替换为 PetWidget）
- `app/application.py`（高 DPI）
- `.github/workflows/auto-release.yml`（feature 分支 prerelease）

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
