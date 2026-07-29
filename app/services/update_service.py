import os
import sys
import tempfile
import subprocess
import requests
import threading
from app.utils.version import is_newer_version
from app.utils.logger import logger

# GitHub 代理镜像列表（按优先级排序，直连失败后自动回退）
GITHUB_PROXY_MIRRORS = [
    "https://ghproxy.com/",
    "https://gh.api.99988866.xyz/",
    "https://github.moeyy.xyz/",
    "https://gh-proxy.com/",
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


class UpdateService:
    APP_NAME = "MiniTools"
    EXE_NAME = "MiniTools.exe"
    GITHUB_API_URL = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
    GITHUB_DOWNLOAD_URL = "https://github.com/uuvccc/WorkDayTimer/releases/latest/download/MiniTools.exe"

    def __init__(self):
        self._download_progress_callback = None
        self._download_complete_callback = None

    def set_callbacks(self, progress_callback=None, complete_callback=None):
        self._download_progress_callback = progress_callback
        self._download_complete_callback = complete_callback

    def get_current_version(self):
        """Get current version from setup.py"""
        try:
            import setup
            return setup.setup.version
        except Exception as e:
            logger.error(f"Error getting current version: {e}")
            return "1.0.0"

    def check_for_updates(self):
        """检查更新，支持 GitHub 代理镜像自动回退"""
        try:
            current_version = self.get_current_version()
            api_urls = _build_proxy_urls(self.GITHUB_API_URL)
            response, used_url = _try_request(api_urls, timeout=15)

            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')

            if is_newer_version(latest_version, current_version):
                return True, latest_version, current_version
            return False, latest_version, current_version
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False, None, self.get_current_version()

    def download_update(self, progress_callback=None):
        """下载更新，支持 GitHub 代理镜像自动回退"""
        callback = progress_callback or self._download_progress_callback

        try:
            download_urls = _build_proxy_urls(self.GITHUB_DOWNLOAD_URL)
            response, used_url = _try_request(download_urls, timeout=30, stream=True)
            logger.info(f"Downloading from: {used_url[:80]}...")

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            temp_dir = tempfile.gettempdir()
            temp_exe_path = os.path.join(temp_dir, f"{self.APP_NAME}_new.exe")

            with open(temp_exe_path, "wb") as exe_file:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        exe_file.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and callback:
                            progress = int((downloaded_size / total_size) * 100)
                            callback(progress, f"Downloading update... {progress}%")
                        elif callback:
                            callback(None, f"Downloading update... {downloaded_size} bytes")

            return True, temp_exe_path, None
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

    def prepare_updater_script(self, temp_exe_path, local_exe_path):
        """Prepare the updater batch script."""
        try:
            updater_script = os.path.join(os.path.dirname(local_exe_path), "updater.bat")
            with open(updater_script, "w") as f:
                f.write(f"""@echo off
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "{os.path.dirname(local_exe_path)}"

timeout /t 3 /nobreak >nul

taskkill /f /im {self.EXE_NAME} 2>nul

icacls "{local_exe_path}" /grant "%USERNAME%":F 2>nul

del "{local_exe_path}" 2>nul
move "{temp_exe_path}" "{local_exe_path}"

set "PATH=%PATH%;C:\\Windows\\System32;C:\\Windows\\SysWOW64"
set "TEMP={os.environ.get('TEMP', '')}"
set "TMP={os.environ.get('TMP', '')}"

icacls "{local_exe_path}" /grant "%USERNAME%":F 2>nul

start "" /D "{os.path.dirname(local_exe_path)}" "{os.path.basename(local_exe_path)}"

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

    def get_download_path(self):
        """Get the path where the update should be downloaded."""
        local_exe_path = sys.argv[0]
        is_running_as_exe = local_exe_path.endswith('.exe')

        if not is_running_as_exe:
            return os.path.join(os.getcwd(), self.EXE_NAME), False

        return local_exe_path, True

update_service = UpdateService()