# PLANS.md

## 当前计划

### 已完成：配置系统重构
- [x] 统一配置到 `settings.json`（替代多个 txt 文件）
- [x] 旧配置自动迁移（`flexible_mode.txt`、`reminder_settings.txt`）
- [x] ConfigManager 支持批量更新 `apply_changes()`

### 已完成：AI 规则体系搭建
- [x] 创建 `AGENTS.md`（AI 入口导航）
- [x] 创建 `ARCHITECTURE.md`（架构文档）
- [x] 创建 `PRODUCT_SENSE.md`（产品认知）
- [x] 创建 `PLANS.md`（本文件）
- [x] 创建 `PROGRESS.md`（进度追踪）
- [x] 创建 `docs/` 目录结构

---

## 待办计划

### 代码质量提升
- [ ] 补充单元测试覆盖率（当前仅 3 个测试文件）
- [ ] 为 `main_window.py` 添加测试（当前无测试）
- [ ] 统一异常处理策略

### 功能增强（候选）
- [ ] 工作时长可自定义（当前硬编码 8.5 小时，已有配置项但 UI 未暴露）
- [ ] 多语言支持（当前仅中文）
- [ ] 托盘气泡通知优化

### 工程化改进（候选）
- [ ] CI 增加 PyInstaller 构建产物自动测试
- [ ] 添加 type hints（当前部分函数缺少）
- [ ] 日志轮转（当前单文件无限增长）

---

## 已完成的历史计划

| 计划 | 完成时间 | 说明 |
|------|---------|------|
| 配置系统重构 | 2025 | settings.json 统一配置 |
| AI 规则体系搭建 | 2026-08 | AGENTS.md + 配套文档 |
