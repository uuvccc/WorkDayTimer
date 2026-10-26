import hashlib
import json
import os
import sys
import shutil
import tempfile
import subprocess
import zipfile
import zlib
import requests
import threading
from urllib.parse import quote

from app.utils.version import is_newer_version
from app.utils.logger import logger

# GitHub 下载代理镜像列表（按优先级排序，直连失败后自动回退）
# 说明：
#  - 这些是社区公益加速服务，随时可能失效；失效后按此格式替换/增删即可。
#  - 此类代理只代理 github.com 的下载/raw 链接，不代理 api.github.com 接口，
#    因此检查更新始终直连 api.github.com（见 check_for_updates）。
GITHUB_PROXY_MIRRORS = [
    "https://ghfast.top/",
    "https://gh-proxy.com/",
    "https://ghproxy.net/",
    "https://gh.llkk.cc/",
    "https://ghp.ci/",
    "https://github.moeyy.xyz/",
]


def _build_proxy_urls(direct_url):
    """为给定的 GitHub URL 生成直连 + 所有代理镜像的 URL 列表"""
    urls = [direct_url]  # 直连排在第一位
    for proxy in GITHUB_PROXY_MIRRORS:
        urls.append(proxy.rstrip("/") + "/" + direct_url)
    return urls


def _try_request(urls, timeout=30, stream=False, method="get"):
    """依次尝试多个 URL，返回第一个成功的响应；全部失败则抛出最后一个异常"""
    last_error = None
    for i, url in enumerate(urls):
        try:
            source = "direct" if i == 0 else f"mirror[{i}]"
            logger.info(f"Trying {source}: {url[:80]}...")
            if method == "get":
                resp = requests.get(url, timeout=timeout, stream=stream)
            else:
                raise ValueError(f"Unsupported method: {method}")
            if resp.status_code == 200:
                return resp, url
            else:
                logger.warning(f"{source} returned HTTP {resp.status_code}")
                last_error = Exception(f"HTTP {resp.status_code} from {source}")
        except Exception as e:
            logger.warning(f"{'direct' if i == 0 else f'mirror[{i}]'} failed: {e}")
            last_error = e
    raise last_error if last_error else Exception("All URLs failed")


def _sha256_file(path):
    """计算文件 sha256（分块读取，避免大文件占内存）。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _select_files_to_fetch(manifest_files, app_dir):
    """挑出需要下载的文件：本地缺失、大小不符或内容（sha256）不符。

    先比大小再算哈希，绝大多数未变化的文件只做一次 stat，避免全量哈希开销。
    """
    to_fetch = []
    for entry in manifest_files:
        rel_path = entry.get("path", "")
        if not rel_path:
            continue
        local_path = os.path.join(app_dir, *rel_path.split("/"))
        if not os.path.isfile(local_path):
            to_fetch.append(entry)
            continue
        if os.path.getsize(local_path) != entry.get("size"):
            to_fetch.append(entry)
            continue
        if _sha256_file(local_path) != entry.get("sha256"):
            to_fetch.append(entry)
    return to_fetch


class UpdateService:
    APP_NAME = "MiniTools"
    EXE_NAME = "MiniTools.exe"
    GITHUB_API_URL = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
    # 发布资产根地址（latest/download）：增量清单、逐文件 .gz 资产与全量 zip 都在这里
    RELEASE_ASSET_BASE = "https://github.com/uuvccc/WorkDayTimer/releases/latest/download"
    # 全量包：增量下载失败时的回退路径
    GITHUB_DOWNLOAD_URL = f"{RELEASE_ASSET_BASE}/MiniTools.zip"
    # 增量更新清单：记录每个文件的大小与 sha256
    MANIFEST_URL = f"{RELEASE_ASSET_BASE}/MiniTools.manifest.json"
    # 需要下载的文件数超过该阈值时直接走全量包：
    # 此时逐文件下载既省不下流量（每个文件一次请求，还失去整包压缩收益），
    # 又容易触发 GitHub 限流。典型场景是从旧 PyInstaller 单 exe 版本首次迁移。
    MAX_INCREMENTAL_FILES = 50

    def __init__(self):
        self._download_progress_callback = None
        self._download_complete_callback = None

    def set_callbacks(self, progress_callback=None, complete_callback=None):
        self._download_progress_callback = progress_callback
        self._download_complete_callback = complete_callback

    def get_current_version(self):
        """Get current version from app/__init__.py.

        无法确定版本时返回 None（而非静默回退到 "1.0.0"），
        否则 current 会被当成旧版本，GitHub latest 永远比它新，
        导致每次启动都误判有更新。
        """
        try:
            from app import __version__
            return __version__
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return None

    def check_for_updates(self):
        """检查更新。

        下载代理镜像（ghfast.top 等）只代理 github.com 的下载/raw 链接，
        不代理 api.github.com 接口，所以这里始终直连 API，避免对无效
        代理做无意义的等待。若直连失败则本次跳过检查（不影响应用运行）。
        """
        try:
            current_version = self.get_current_version()
            if not current_version:
                logger.warning("Cannot determine current version, skipping update check")
                return False, None, None
            logger.info(f"Checking for updates, current version: {current_version}")
            response = requests.get(self.GITHUB_API_URL, timeout=15)
            response.raise_for_status()
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')

            if is_newer_version(latest_version, current_version):
                return True, latest_version, current_version
            return False, latest_version, current_version
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None, self.get_current_version()

    def download_update(self, progress_callback=None):
        """下载更新：优先逐文件增量，任何环节失败都自动回退到全量 zip。

        返回 (成功, 暂存目录, 错误信息)。暂存目录内容：
        - 增量成功：只含与本地不同的文件（安装时复制这些文件即等价于增量更新）
        - 回退全量：完整的新版本目录
        """
        callback = progress_callback or self._download_progress_callback

        # 源码运行时目录结构与应用目录不同，无法用 manifest 比对，直接走全量
        if getattr(sys, 'frozen', False):
            success, staging_dir, error = self._download_incremental(callback)
            if success:
                return True, staging_dir, None
            logger.warning(f"Incremental update failed: {error}. Falling back to full package.")

        return self._download_full(callback)

    def _download_incremental(self, callback):
        """按 manifest 逐文件增量下载，返回 (成功, 暂存目录, 错误信息)。"""
        staging_dir = os.path.join(tempfile.gettempdir(), f"{self.APP_NAME}_patch_extract")
        try:
            manifest = self._fetch_manifest()
            if manifest is None:
                return False, None, "cannot fetch update manifest"

            manifest_files = manifest.get("files") or []
            app_dir = os.path.dirname(sys.executable)
            to_fetch = _select_files_to_fetch(manifest_files, app_dir)
            total = len(to_fetch)
            logger.info(
                f"Incremental update: {total}/{len(manifest_files)} file(s) need download "
                f"(manifest version {manifest.get('version')})"
            )
            if total == 0:
                return False, None, "no files differ from manifest"
            if total > self.MAX_INCREMENTAL_FILES:
                return False, None, (
                    f"too many files differ ({total} > {self.MAX_INCREMENTAL_FILES}), "
                    "using full package"
                )

            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            os.makedirs(staging_dir, exist_ok=True)

            for index, entry in enumerate(to_fetch, start=1):
                label = f"Downloading update... {index}/{total} files"
                if callback:
                    callback(int((index - 1) * 100 / total), label)
                self._fetch_asset(entry, staging_dir)
                if callback:
                    callback(int(index * 100 / total), label)

            return True, staging_dir, None
        except Exception as e:
            shutil.rmtree(staging_dir, ignore_errors=True)
            error = f"incremental download failed: {e}"
            logger.warning(error)
            return False, None, error

    def _fetch_manifest(self):
        """下载并解析增量清单；失败返回 None（由调用方回退全量）。"""
        try:
            response, _used_url = _try_request(_build_proxy_urls(self.MANIFEST_URL), timeout=15)
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get("files"), list):
                logger.warning("Manifest has unexpected structure, ignoring")
                return None
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch update manifest: {e}")
            return None

    def _fetch_asset(self, entry, staging_dir):
        """下载单个 .gz 资产并解压到暂存目录，同时校验大小与 sha256。"""
        asset_url = f"{self.RELEASE_ASSET_BASE}/{quote(entry['asset'])}"
        target_path = os.path.join(staging_dir, *entry["path"].split("/"))
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        response, _used_url = _try_request(_build_proxy_urls(asset_url), timeout=60, stream=True)
        try:
            digest = hashlib.sha256()
            written = 0
            # gzip 流式解压：16 + MAX_WBITS 表示数据带 gzip 头
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            with open(target_path, "wb") as out:
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    data = decompressor.decompress(chunk)
                    if data:
                        out.write(data)
                        digest.update(data)
                        written += len(data)
                tail = decompressor.flush()
                if tail:
                    out.write(tail)
                    digest.update(tail)
                    written += len(tail)
        finally:
            response.close()

        if written != entry.get("size") or digest.hexdigest() != entry.get("sha256"):
            os.remove(target_path)
            raise ValueError(
                f"integrity check failed for {entry['path']} "
                f"(expected {entry.get('size')} bytes, got {written})"
            )

    def _download_full(self, callback):
        """全量回退：下载完整 zip 并解压，返回 (成功, 解压目录, 错误信息)。"""
        try:
            download_urls = _build_proxy_urls(self.GITHUB_DOWNLOAD_URL)
            response, used_url = _try_request(download_urls, timeout=30, stream=True)
            logger.info(f"Downloading from: {used_url[:80]}...")

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            temp_dir = tempfile.gettempdir()
            temp_zip_path = os.path.join(temp_dir, f"{self.APP_NAME}_new.zip")

            with open(temp_zip_path, "wb") as zip_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        zip_file.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and callback:
                            progress = int((downloaded_size / total_size) * 100)
                            callback(progress, f"Downloading update... {progress}%")
                        elif callback:
                            callback(None, f"Downloading update... {downloaded_size} bytes")

            # 校验 1：文件大小与服务器声明一致（代理可能中途截断）
            if total_size > 0 and downloaded_size != total_size:
                os.remove(temp_zip_path)
                error = (f"Download incomplete: expected {total_size} bytes, "
                         f"got {downloaded_size} bytes.")
                logger.error(error)
                return False, None, error

            # 校验 2：必须是以 PK 开头的 zip 文件，
            # 防止代理返回 200 + HTML 错误页时把垃圾内容当作更新包。
            with open(temp_zip_path, "rb") as f:
                if f.read(2) != b"PK":
                    os.remove(temp_zip_path)
                    error = ("Downloaded file is not a valid zip archive "
                             "(the proxy may have returned an error page).")
                    logger.error(error)
                    return False, None, error

            # 解压到临时目录
            temp_extract_dir = os.path.join(temp_dir, f"{self.APP_NAME}_new_extract")
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir, exist_ok=True)

            with zipfile.ZipFile(temp_zip_path, "r") as zf:
                zf.extractall(temp_extract_dir)

            # 校验 3：解压后必须包含 MiniTools.exe，防止 zip 内容异常
            extracted_exe = os.path.join(temp_extract_dir, self.EXE_NAME)
            if not os.path.isfile(extracted_exe):
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                os.remove(temp_zip_path)
                error = "Update package is invalid: MiniTools.exe not found after extraction."
                logger.error(error)
                return False, None, error

            os.remove(temp_zip_path)
            return True, temp_extract_dir, None
        except requests.exceptions.Timeout:
            error = "Download timed out. Please check your network connection and try again."
            logger.error(error)
            return False, None, error
        except requests.exceptions.RequestException as e:
            error = f"Network error: {str(e)}"
            logger.error(error)
            return False, None, error
        except Exception as e:
            error = f"An error occurred: {str(e)}"
            logger.error(error)
            return False, None, error

    def prepare_updater_script(self, temp_dir, local_exe_path):
        """生成更新脚本（复制暂存目录内容到应用目录）。

        temp_dir: 暂存目录。增量下载时只含与本地有差异的文件；回退全量时
                  是完整的新版本目录。两种情况都用同一套复制逻辑。
        local_exe_path: 当前运行的 exe 路径（应用目录）

        更新策略：用 robocopy /E 把暂存目录内容复制到应用目录。
        - 暂存目录中存在的文件：覆盖旧版本
        - 暂存目录中不存在的文件：保留（用户的 settings.json、自定义动画/图片、
          logs/ 等不会被删除）
        - 旧版本中已删除的文件：会残留（小项目可接受，避免误删用户数据）
        """
        try:
            app_dir = os.path.dirname(local_exe_path)
            updater_script = os.path.join(app_dir, "updater.bat")
            with open(updater_script, "w") as f:
                f.write(f"""@echo off
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "{app_dir}"

timeout /t 3 /nobreak >nul

taskkill /f /im {self.EXE_NAME} 2>nul
timeout /t 1 /nobreak >nul

:: robocopy /E：复制所有子目录与文件，覆盖同名文件，
:: 不删除目标中源没有的文件（保留用户配置与自定义资源）
robocopy "{temp_dir}" "{app_dir}" /E /IS /IT /R:2 /W:1 >nul

set "PATH=%PATH%;C:\\Windows\\System32;C:\\Windows\\SysWOW64"
set "TEMP={os.environ.get('TEMP', '')}"
set "TMP={os.environ.get('TMP', '')}"

start "" /D "{app_dir}" "{os.path.basename(local_exe_path)}"

:: 清理临时解压目录与自身
rmdir /s /q "{temp_dir}" 2>nul

del "%~f0"
""")
            return updater_script
        except Exception as e:
            logger.error(f"Error preparing updater script: {e}")
            return None

    def run_updater(self, updater_script):
        """Run the updater script."""
        try:
            env = os.environ.copy()
            env['PATH'] = env.get('PATH', '') + r';C:\Windows\System32;C:\Windows\SysWOW64'
            env['TEMP'] = os.environ.get('TEMP', '')
            env['TMP'] = os.environ.get('TMP', '')
            subprocess.Popen(updater_script, shell=True, env=env)
            return True, "Updater started successfully."
        except Exception as e:
            error = f"Error running updater: {e}"
            logger.error(error)
            return False, error

    def get_local_exe_path(self):
        """获取当前运行的 exe 路径（更新替换目标）。"""
        return sys.executable

update_service = UpdateService()