import os
import sys
import logging
import tempfile
import threading
import subprocess
import hashlib
import json

import requests
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal, QObject
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox, QCheckBox, QHBoxLayout

from workday_timer.config import config


class UpdateConfig:
    """更新配置管理类"""
    def __init__(self):
        self.check_interval = 24 * 60 * 60  # 默认每24小时检查一次
        self.auto_check = True  # 默认自动检查更新
        self.auto_download = False  # 默认不自动下载
        self.update_history_file = os.path.join(config.base_dir, "update_history.json")
        self._load_config()
    
    def _load_config(self):
        """加载更新配置"""
        config_file = os.path.join(config.base_dir, "update_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.check_interval = data.get('check_interval', self.check_interval)
                    self.auto_check = data.get('auto_check', self.auto_check)
                    self.auto_download = data.get('auto_download', self.auto_download)
            except Exception as e:
                logging.error(f"加载更新配置失败: {e}")
    
    def save_config(self):
        """保存更新配置"""
        config_file = os.path.join(config.base_dir, "update_config.json")
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'check_interval': self.check_interval,
                    'auto_check': self.auto_check,
                    'auto_download': self.auto_download
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存更新配置失败: {e}")
    
    def add_update_history(self, version, timestamp, status):
        """添加更新历史记录"""
        history = []
        if os.path.exists(self.update_history_file):
            try:
                with open(self.update_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logging.error(f"加载更新历史失败: {e}")
        
        history.append({
            'version': version,
            'timestamp': timestamp,
            'status': status
        })
        
        # 只保留最近10条记录
        history = history[-10:]
        
        try:
            os.makedirs(os.path.dirname(self.update_history_file), exist_ok=True)
            with open(self.update_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"保存更新历史失败: {e}")


class UpdateChecker:
    """更新检查器"""
    def __init__(self, current_version):
        self.current_version = current_version
        self.api_url = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
    
    def check(self):
        """检查更新"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                download_url = release_data['assets'][0]['browser_download_url'] if release_data.get('assets') else None
                release_notes = release_data.get('body', '')
                
                if self._is_newer_version(latest_version, self.current_version):
                    return {
                        'available': True,
                        'version': latest_version,
                        'download_url': download_url,
                        'release_notes': release_notes
                    }
            return {'available': False}
        except Exception as e:
            logging.error(f"检查更新失败: {e}")
            return {'available': False, 'error': str(e)}
    
    def _is_newer_version(self, latest, current):
        """比较版本号"""
        try:
            latest_parts = list(map(int, latest.split('.')))
            current_parts = list(map(int, current.split('.')))
            
            max_length = max(len(latest_parts), len(current_parts))
            while len(latest_parts) < max_length:
                latest_parts.append(0)
            while len(current_parts) < max_length:
                current_parts.append(0)
            
            for l, c in zip(latest_parts, current_parts):
                if l > c:
                    return True
                elif l < c:
                    return False
            return False
        except Exception:
            return False


class UpdateDownloader(QObject):
    """更新下载器"""
    progress_updated = pyqtSignal(int, str)  # 进度, 状态文本
    download_completed = pyqtSignal(bool, str)  # 成功, 错误信息
    
    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
        self.cancelled = False
    
    def start(self):
        """开始下载"""
        threading.Thread(target=self._download, daemon=True).start()
    
    def cancel(self):
        """取消下载"""
        self.cancelled = True
    
    def _download(self):
        """下载文件"""
        try:
            if self.download_url.startswith('file://'):
                # 本地文件处理
                self._download_local_file()
            else:
                # 远程文件下载
                self._download_remote_file()
        except Exception as e:
            logging.error(f"下载失败: {e}")
            self.download_completed.emit(False, f"下载失败: {str(e)}")
    
    def _download_local_file(self):
        """下载本地文件"""
        import shutil
        local_file_path = self.download_url.replace('file:///', '').replace('/', '\\')
        
        if not os.path.exists(local_file_path):
            self.download_completed.emit(False, f"本地文件不存在: {local_file_path}")
            return
        
        total_size = os.path.getsize(local_file_path)
        downloaded_size = 0
        chunk_size = 4096
        
        with open(self.save_path, "wb") as exe_file:
            with open(local_file_path, "rb") as src_file:
                while True:
                    if self.cancelled:
                        self.download_completed.emit(False, "下载已取消")
                        return
                    
                    chunk = src_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    exe_file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = int((downloaded_size / total_size) * 100)
                    self.progress_updated.emit(progress, f"复制更新文件... {progress}%")
        
        self.download_completed.emit(True, "")
    
    def _download_remote_file(self):
        """下载远程文件"""
        response = requests.get(self.download_url, stream=True, timeout=30)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 8192  # 增大块大小以提高下载速度
            
            with open(self.save_path, "wb") as exe_file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.cancelled:
                        self.download_completed.emit(False, "下载已取消")
                        return
                    
                    if chunk:
                        exe_file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_updated.emit(progress, f"下载更新... {progress}%")
                        else:
                            self.progress_updated.emit(0, f"下载更新... {downloaded_size} bytes")
            
            self.download_completed.emit(True, "")
        else:
            self.download_completed.emit(False, f"下载失败，HTTP状态码: {response.status_code}")


class UpdateInstaller:
    """更新安装器"""
    def __init__(self, temp_exe_path, local_exe_path):
        self.temp_exe_path = temp_exe_path
        self.local_exe_path = local_exe_path
        self.is_running_as_exe = local_exe_path.endswith('.exe')
    
    def install(self):
        """安装更新"""
        if not self.is_running_as_exe:
            return self._install_as_script()
        else:
            return self._install_as_exe()
    
    def _install_as_script(self):
        """以脚本模式安装"""
        try:
            import shutil
            shutil.move(self.temp_exe_path, self.local_exe_path)
            return True, f"可执行文件下载成功！\n位置: {self.local_exe_path}\n运行此文件以启动应用程序。"
        except Exception as e:
            return False, f"移动下载文件失败: {e}"
    
    def _install_as_exe(self):
        """以可执行文件模式安装"""
        try:
            updater_script = os.path.join(os.path.dirname(self.local_exe_path), "updater.bat")
            
            # 确保路径使用反斜杠
            local_exe_path_batch = self.local_exe_path.replace('/', '\\')
            temp_exe_path_batch = self.temp_exe_path.replace('/', '\\')
            exe_dir_batch = os.path.dirname(self.local_exe_path).replace('/', '\\')
            exe_name_batch = os.path.basename(self.local_exe_path)
            
            with open(updater_script, "w") as f:
                f.write(f"""@echo off
 :: 切换到可执行文件目录
 cd /d "{exe_dir_batch}"

 :: 创建日志文件
 echo Updater started > updater.log
 echo Local exe path: {local_exe_path_batch} >> updater.log
 echo Temp exe path: {temp_exe_path_batch} >> updater.log
 echo Current directory: %CD% >> updater.log

 :: 等待旧进程完全退出
 echo Waiting for old process to exit... >> updater.log
 timeout /t 5 /nobreak >nul

 :: 终止任何剩余的实例
 echo Killing remaining instances... >> updater.log
 taskkill /f /im WorkDayTimer.exe 2>>updater.log

 :: 等待资源释放
 echo Waiting for resources to be released... >> updater.log
 timeout /t 2 /nobreak >nul

 :: 检查文件是否存在
 echo Checking if files exist... >> updater.log
 if exist "{local_exe_path_batch}" (
     echo Old executable exists >> updater.log
 ) else (
     echo Old executable does not exist >> updater.log
 )

 if exist "{temp_exe_path_batch}" (
     echo New executable exists >> updater.log
 ) else (
     echo New executable does not exist >> updater.log
 )

 :: 删除旧可执行文件
 echo Deleting old executable... >> updater.log
 del "{local_exe_path_batch}" 2>>updater.log

 :: 移动新可执行文件
 echo Moving new executable... >> updater.log
 move "{temp_exe_path_batch}" "{local_exe_path_batch}" 2>>updater.log

 :: 检查移动是否成功
 if exist "{local_exe_path_batch}" (
     echo Move successful >> updater.log
 ) else (
     echo Move failed >> updater.log
 )

 :: 设置PATH环境变量
 set "PATH=%PATH%;C:\Windows\System32;C:\Windows\SysWOW64"

 :: 清除可能干扰的环境变量
 set PYTHONPATH=
 set TEMP=%TEMP%
 set TMP=%TMP%

 :: 启动新的可执行文件
 echo Starting new executable... >> updater.log
 start "" "{exe_name_batch}"

 :: 等待后删除脚本
 timeout /t 2 /nobreak >nul
 echo Deleting updater script... >> updater.log
 del "%~f0"
 """)
            
            # 设置脚本执行权限
            os.chmod(updater_script, 0o755)
            
            # 启动更新脚本
            env = os.environ.copy()
            env['PATH'] = env.get('PATH', '') + r';C:\Windows\System32;C:\Windows\SysWOW64'
            subprocess.Popen(updater_script, shell=True, env=env, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            
            return True, "更新安装脚本已启动，应用程序将自动重启。"
        except Exception as e:
            return False, f"创建更新脚本失败: {e}"


class UpdateUI(QDialog):
    """更新用户界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("更新进度")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.resize(400, 150)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("准备下载更新...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def update_progress(self, progress, status_text):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status_text)
    
    def set_indeterminate(self, status_text):
        """设置不确定进度"""
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(status_text)


class UpdateConfigUI(QDialog):
    """更新配置界面"""
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("更新设置")
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # 自动检查更新选项
        self.auto_check_checkbox = QCheckBox("自动检查更新")
        self.auto_check_checkbox.setChecked(self.config.auto_check)
        layout.addWidget(self.auto_check_checkbox)
        
        # 自动下载更新选项
        self.auto_download_checkbox = QCheckBox("自动下载更新")
        self.auto_download_checkbox.setChecked(self.config.auto_download)
        layout.addWidget(self.auto_download_checkbox)
        
        # 更新检查间隔选项
        interval_layout = QHBoxLayout()
        interval_label = QLabel("检查间隔 (小时):")
        interval_layout.addWidget(interval_label)
        
        from PyQt5.QtWidgets import QSpinBox
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 168)  # 1小时到7天
        self.interval_spinbox.setValue(self.config.check_interval // 3600)
        interval_layout.addWidget(self.interval_spinbox)
        layout.addLayout(interval_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 连接信号
        self.save_button.clicked.connect(self.save_config)
        self.cancel_button.clicked.connect(self.reject)
    
    def save_config(self):
        """保存配置"""
        self.config.auto_check = self.auto_check_checkbox.isChecked()
        self.config.auto_download = self.auto_download_checkbox.isChecked()
        self.config.check_interval = self.interval_spinbox.value() * 3600
        self.config.save_config()
        self.accept()


class UpdateHistoryUI(QDialog):
    """更新历史界面"""
    def __init__(self, history_file, parent=None):
        super().__init__(parent)
        self.history_file = history_file
        self.setWindowTitle("更新历史")
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        from PyQt5.QtWidgets import QTextEdit
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)
        
        self.load_history()
        
        self.ok_button = QPushButton("确定")
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.accept)
    
    def load_history(self):
        """加载更新历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    import json
                    history = json.load(f)
                    history_text = "更新历史记录:\n\n"
                    for item in reversed(history):  # 倒序显示，最新的在前面
                        timestamp = item.get('timestamp', '')
                        version = item.get('version', '未知版本')
                        status = item.get('status', '未知状态')
                        history_text += f"时间: {timestamp}\n版本: {version}\n状态: {status}\n\n"
                    self.history_text.setText(history_text)
            except Exception as e:
                self.history_text.setText(f"加载更新历史失败: {e}")
        else:
            self.history_text.setText("暂无更新历史记录")


class Updater:
    """自动更新管理器"""
    def __init__(self, app):
        self.app = app
        self.current_version = self._get_current_version()
        self.config = UpdateConfig()
        self.checker = UpdateChecker(self.current_version)
        self.downloader = None
        self.installer = None
        self.ui = None
    
    def _get_current_version(self):
        """获取当前版本"""
        try:
            import importlib.util
            setup_path = os.path.join(config.base_dir, "setup.py")
            spec = importlib.util.spec_from_file_location("setup", setup_path)
            setup = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(setup)
            return setup.__version__
        except Exception as e:
            logging.error(f"获取当前版本失败: {e}")
            return "0.0.0"
    
    def check_for_updates(self, show_no_update=False):
        """检查更新"""
        logging.info("检查更新...")
        result = self.checker.check()
        
        if result['available']:
            self._show_update_notification(result)
        elif show_no_update:
            QMessageBox.information(self.app, "检查更新", "当前已是最新版本。")
        
        return result
    
    def _show_update_notification(self, update_info):
        """显示更新通知"""
        msg_box = QMessageBox(self.app)
        msg_box.setWindowTitle("发现新版本")
        msg_box.setText(f"发现新版本: {update_info['version']}\n\n更新内容:\n{update_info['release_notes'][:500]}...")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        
        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            self.download_and_install(update_info)
    
    def download_and_install(self, update_info):
        """下载并安装更新"""
        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        temp_exe_path = os.path.join(temp_dir, f"WorkDayTimer_{update_info['version']}.exe")
        
        # 确定本地可执行文件路径
        local_exe_path = sys.argv[0]
        if not local_exe_path.endswith('.exe'):
            local_exe_path = os.path.join(os.getcwd(), "WorkDayTimer.exe")
        
        # 显示下载UI
        self.ui = UpdateUI(self.app)
        self.ui.show()
        
        # 创建下载器
        self.downloader = UpdateDownloader(update_info['download_url'], temp_exe_path)
        self.downloader.progress_updated.connect(self.ui.update_progress)
        self.downloader.download_completed.connect(lambda success, error: self._on_download_completed(success, error, temp_exe_path, local_exe_path, update_info['version']))
        self.ui.cancel_button.clicked.connect(self.downloader.cancel)
        
        # 开始下载
        self.downloader.start()
    
    def _on_download_completed(self, success, error, temp_exe_path, local_exe_path, version):
        """下载完成回调"""
        if self.ui:
            self.ui.close()
        
        if not success:
            QMessageBox.critical(self.app, "下载失败", error)
            return
        
        # 验证文件完整性
        if not self._verify_file_integrity(temp_exe_path):
            QMessageBox.critical(self.app, "验证失败", "更新文件完整性验证失败，可能是下载过程中出现了问题。")
            return
        
        # 安装更新
        self.installer = UpdateInstaller(temp_exe_path, local_exe_path)
        install_success, install_message = self.installer.install()
        
        if install_success:
            # 记录更新历史
            import datetime
            self.config.add_update_history(version, datetime.datetime.now().isoformat(), "success")
            
            if local_exe_path.endswith('.exe'):
                # 对于可执行文件模式，应用程序将自动重启
                self.app.quit()
            else:
                QMessageBox.information(self.app, "更新完成", install_message)
        else:
            QMessageBox.critical(self.app, "安装失败", install_message)
            # 记录更新历史
            import datetime
            self.config.add_update_history(version, datetime.datetime.now().isoformat(), "failed")
    
    def _verify_file_integrity(self, file_path):
        """验证文件完整性"""
        try:
            # 这里可以实现更复杂的验证，如MD5校验等
            # 目前只是检查文件是否存在且大小合理
            if os.path.exists(file_path) and os.path.getsize(file_path) > 10 * 1024 * 1024:  # 至少10MB
                return True
            return False
        except Exception as e:
            logging.error(f"验证文件完整性失败: {e}")
            return False
    
    def get_update_config(self):
        """获取更新配置"""
        return self.config
    
    def set_update_config(self, config):
        """设置更新配置"""
        self.config = config
        self.config.save_config()
    
    def show_config_ui(self):
        """显示更新配置界面"""
        config_ui = UpdateConfigUI(self.config, self.app)
        config_ui.exec_()
    
    def show_history_ui(self):
        """显示更新历史界面"""
        history_ui = UpdateHistoryUI(self.config.update_history_file, self.app)
        history_ui.exec_()


def check_for_updates(app):
    """检查更新的便捷函数"""
    updater = Updater(app)
    if updater.config.auto_check:
        updater.check_for_updates()


def update_application(app):
    """更新应用程序的便捷函数"""
    updater = Updater(app)
    updater.check_for_updates(show_no_update=True)
