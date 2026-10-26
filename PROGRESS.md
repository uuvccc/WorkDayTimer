# PROGRESS.md

## 当前状态

**最新完成**：增量更新——manifest 比对 + 逐文件 .gz 下载，典型更新下载量 22.8MB → ~4.5MB，失败自动回退全量包（2026-10）

---

## 变更日志

### 2026-10 — 增量更新（manifest 方案）

**背景**：standalone 产物每次更新都要下载完整 22.8MB zip，而实际变化通常只有 `MiniTools.exe`（压缩后 4.46MB）和少数资源文件。

**改动**：
- `build.py` — 新增 `make_manifest_and_assets()`：生成 `dist/MiniTools.manifest.json`（每个文件 path/asset/size/sha256）与 `dist/assets/*.gz`（逐文件 gzip 资产，路径中的 `/` 扁平化为 `__`）
- `app/services/update_service.py` — 新增 `_download_incremental()`：拉 manifest → `_select_files_to_fetch()` 按 size/sha256 比对本地 → 只下载差异文件的 `.gz` 并解压校验；任一环节失败（含 manifest 404、单文件校验失败、无差异文件）自动回退 `_download_full()`
- `app/services/update_service.py` — 新增模块级纯函数 `_sha256_file()` / `_select_files_to_fetch()`，便于单测；增量只对 `sys.frozen` 生效，源码运行直接走全量
- `tests/test_update_service.py`（新建）— 8 个单测：哈希一致性、缺失/大小不符/同大小不同内容均需重下、嵌套路径解析、混合清单只返回差异项
- `.github/workflows/auto-release.yml` — release 改为 draft 流程（建 draft → 上传 manifest/zip/全部 .gz（每批 20 个）→ 发布），避免 `releases/latest` 在资产未齐时被客户端读到
- `.github/workflows/python-app.yml` — 构建产物增加 manifest 上传
- `AGENTS.md` — 更新机制补充增量流程，新增「打包与发布约定」章节

**效果**：仅 exe 变化的常规版本更新下载约 **4.5MB**（原 22.81MB，降约 80%）；增量安装用 robocopy 复制暂存目录，实际只写变化文件。

**已知边界**：
- 增量安装不删除旧版本已移除的文件（残留文件不影响运行，重新完整安装可清理）
- 从旧 PyInstaller 单 exe 版本升级时，manifest 判定全部文件缺失 → 自动退化为全量下载，符合预期

---

### 2026-10 — 打包工具从 PyInstaller 切换为 Nuitka standalone

**背景**：用户要求资源文件不再释放到临时目录，编译产物改为压缩包形式，更新方式同步调整。

**改动**：
- `build.py`（新建）— Nuitka standalone 统一构建入口：编译 main.py → 打包 `dist/main.dist/` 为 `dist/MiniTools.zip`；显式 nofollow 未用 Qt 模块
- `app/config/constants.py` — `get_resource_dir()` 不再使用 `sys._MEIPASS`（PyInstaller 专属），Nuitka standalone 下资源直接放在 exe 旁
- `app/services/update_service.py` — 下载目标从 exe 改为 zip；校验改为 zip 头 PK 魔数 + 解压后必须包含 MiniTools.exe；updater.bat 改为 robocopy /E 覆盖式复制（保留用户配置/自定义资源，不删除目标中源没有的文件）
- `app/utils/logger.py` / `app/ui/ascii_art.py` — 注释更新（PyInstaller → Nuitka）
- `MiniTools.spec` — 删除（不再使用 PyInstaller）
- `.gitignore` — 移除 `!MiniTools.spec` 白名单，添加 Nuitka 忽略项（`*.build` / `*.dist` / `*.onefile-build`）
- `.github/workflows/python-app.yml` / `auto-release.yml` — 构建工具从 `pyinstaller` 改为 `nuitka`；构建命令从 `pyinstaller MiniTools.spec` 改为 `python build.py`；release 资产从 `MiniTools.exe` 改为 `MiniTools.zip`
- `AGENTS.md` — 技术栈、开发命令、更新机制、路径解析说明同步更新

**效果**：standalone 模式下资源文件不再解压到临时目录，启动无需等待解压；发布产物为 zip 压缩包，更新时下载 zip 解压覆盖即可。

---

### 2026-10 — 发布产物瘦身（减小每次更新的下载体积）

**背景**：解包实测 v1.0.0.113（46.98MB）：Qt5/Qt DLL 占 52%，其中 opengl32sw.dll（7.4MB，软件 OpenGL 回退）、Qt5Quick/Qml、Qt5Network+OpenSSL 等均未使用；numpy 占 16%（7.4MB）但仅用于 `image.py` 的图片透明化；资源文件（动画+图片）仅占 0.3%，分离资源对更新体积无意义。

**改动**：
- `app/utils/image.py` — 移除 numpy，改为纯 Python 实现（BFS flood fill 替代迭代膨胀；距离平方比较避免每像素开方）。新旧实现逐字节对比零差异（真实图片 + 5 组合成图），且新实现更快
- `MiniTools.spec` — `excludes` 排除 29 个未用 Qt 模块；按文件名前缀过滤大型无关 DLL（opengl32sw/ANGLE/OpenSSL/Qt5Quick 等）；平台插件只留 `qwindows.dll`；剔除 Qt 翻译文件
- `requirements.txt` / `AGENTS.md` — 移除 numpy
- `tests/test_image.py` — 新增 5 个语义测试（边缘背景透明、内容保留、白色孤岛不透明、全白图、缺文件不崩溃）

**效果**：本地构建 53.8MB → 23.0MB（-57%）；冒烟测试通过（完整初始化无报错）。注意 **UPX 未启用**：CI 无 upx 且 onefile 已 zlib 压缩，UPX 增益有限且有杀软误报风险。

---

### 2026-10 — 打包工程化现代化

**改动**：
- 构建入口收敛：`MiniTools.spec` 成为唯一打包入口（onefile/windowed/icon/datas 全在 spec 内），CI 与本地统一 `pyinstaller MiniTools.spec`；删除 `workday_timer.spec` 与 CI 命令行参数
- 构建工具固定大版本区间：`pyinstaller>=6.10,<7`、`flake8>=7.0,<8`（两个 workflow 一致）
- CI 弃用组件替换：`setup-python@v3` → `@v5`；`create-release@v1` + `upload-release-asset@v1`（已归档）→ `gh release create`；`::set-output`（GitHub 已禁用）→ `$GITHUB_OUTPUT`
- `python-app.yml` 改为纯校验流水线（lint + test + spec 构建验证），去掉 release 触发与资产上传（避免与 auto-release 重复上传），permissions 降为 `contents: read`
- 删除 `setup.py`（exe-only 后无消费者，字段陈旧），「禁止 import setup」的坑从根源消除；版本继续从 `app/__init__.py` 读取
- 文档同步：AGENTS.md / README.md / README_CN.md 打包命令与目录树更新
- **修复**：`.gitignore` 的 `*.spec` 规则导致 `MiniTools.spec` 从未入库，CI 检出后找不到 spec 直接构建失败；已加 `!MiniTools.spec` 白名单并纳入版本控制（教训：改用 spec 作为构建入口前，先确认该文件在版本控制中）

---

### 2026-10 — 全项目废弃脚本模式（仅发布 exe）

**决策**：只使用 exe 版本，脚本模式不再是用户可用的运行方式；开发/测试仍从源码运行。

**改动**：
- `system_service.py` — 删除 `get_exe_path()` / `is_running_as_exe()`，开机自启命令固定为 `sys.executable`（移除 pythonw 脚本分支）
- `update_service.py` — `get_download_path()` 改为 `get_local_exe_path()`，直接返回 `sys.executable`
- `main_window.py` — 更新流程移除「脚本模式下载到当前目录」确认弹窗与 shutil.move 安装分支，统一走 updater.bat
- `constants.py` / `logger.py` 的 frozen 路径判断**保留**（源码运行开发/测试仍需要），文档表述改为「源码运行」
- AGENTS.md / ascii_animations/README.md 同步更新为 exe-only 说明

---

### 2026-10 — ASCII 动画全部外置为文件

**问题**：49 个内置 ASCII 场景硬编码在 `app/ui/ascii_art.py` 的 `SCENES` 字典里（约 1200 行），
与 `ascii_animations/` 文件夹里的用户自定义动画两套体系并存，维护割裂。

**改动**：
- 内置场景全部导出为 `ascii_animations/*.json`（49 个；clock/celebrate/sleepy 等状态场景标记 `idle: false`，行为不变），与用户自定义动画放同一文件夹
- `ascii_art.py` 移除硬编码字典，启动时统一从动画文件加载：exe 模式默认动画由 `--add-data` 打包进 exe（`sys._MEIPASS` 只读），用户目录同名文件覆盖默认；脚本模式两者本就是同一目录
- `main_window.py` 增加兜底：场景文件被删/未加载时回退待机场景或图片模式，不再假设场景名必然存在
- CI（auto-release.yml）与 MiniTools.spec / workday_timer.spec 打包参数加上 `ascii_animations` 目录
- 更新 `ascii_animations/README.md` 说明内置默认 + 用户自定义的双来源加载规则

---

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
