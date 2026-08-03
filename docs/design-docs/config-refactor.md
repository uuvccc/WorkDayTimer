# 配置系统重构

## 背景

早期配置分散在多个 txt 文件中：
- `flexible_mode.txt` — 灵活模式状态
- `reminder_settings.txt` — 提醒开关设置

这种方式难以扩展，且读写逻辑分散。

## 目标

- 统一配置到单一 JSON 文件
- 支持向后兼容（自动迁移旧配置）
- 提供批量更新接口

## 方案

### 配置文件

`settings.json` 结构：

```json
{
  "flexible_mode": false,
  "run_on_startup": false,
  "work_hours": 8.5,
  "fixed_start_hour": 9.0,
  "job_record_before_end_minutes": 60,
  "reminders": {
    "checkin_reminder": true,
    "job_record_reminder": true,
    "checkout_reminder": true
  }
}
```

### 迁移逻辑

ConfigManager 启动时检查：
1. 若 `settings.json` 已存在 → 直接加载
2. 若不存在且旧文件存在 → 读取旧文件 → 写入 `settings.json` → 删除旧文件

### 接口设计

- Property setter 自动持久化（`config.is_flexible = True`）
- 批量更新：`apply_changes(flexible_mode=True, work_hours=9.0)`

## 影响范围

- `app/config/constants.py` — 新增 `SETTINGS_FILE`、`DEFAULT_SETTINGS`
- `app/config/manager.py` — 重写为 JSON 读写 + 迁移逻辑
- 删除对 `flexible_mode.txt`、`reminder_settings.txt` 的直接读写
