import os
import sys
import logging
import tempfile
import threading
import subprocess

import requests
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton

from workday_timer.config import config


def check_for_updates(app):
    """Check for updates from GitHub."""
    try:
        # Get current version from setup.py
        import importlib.util
        setup_path = os.path.join(config.base_dir, "setup.py")
        spec = importlib.util.spec_from_file_location("setup", setup_path)
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        current_version = setup.setup.version
        
        # Get latest version from GitHub API
        api_url = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            
            # Compare versions
            if _is_newer_version(latest_version, current_version):
                # Show update notification in the main thread
                from PyQt5.QtWidgets import QApplication
                QApplication.postEvent(app, QEvent(QEvent.User))
    except Exception as e:
        # Silent error handling to avoid disrupting the app
        logging.error(f"Error checking for updates: {e}")


def _is_newer_version(latest, current):
    """Compare version strings to determine if a new version is available."""
    try:
        # Split version strings into components
        latest_parts = list(map(int, latest.split('.')))
        current_parts = list(map(int, current.split('.')))
        
        # Pad with zeros to make lengths equal
        max_length = max(len(latest_parts), len(current_parts))
        while len(latest_parts) < max_length:
            latest_parts.append(0)
        while len(current_parts) < max_length:
            current_parts.append(0)
        
        # Compare each component
        for l, c in zip(latest_parts, current_parts):
            if l > c:
                return True
            elif l < c:
                return False
        return False
    except Exception:
        # If version parsing fails, assume no update
        return False


def update_application(app):
    """Download the latest executable from GitHub and replace the current one."""
    try:
        github_url = "https://github.com/uuvccc/WorkDayTimer/releases/latest/download/WorkDayTimer.exe"
        
        # Determine if running as executable or script
        local_exe_path = sys.argv[0]
        is_running_as_exe = local_exe_path.endswith('.exe')
        
        if not is_running_as_exe:
            # When running as script, download to current directory
            local_exe_path = os.path.join(os.getcwd(), "WorkDayTimer.exe")
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(app, "Update Confirmation", 
                                       "Application is running as a Python script.\n"
                                       "The executable will be downloaded to the current directory.\n"
                                       f"Download location: {local_exe_path}\n"
                                       "Do you want to continue?")
            if reply != QMessageBox.Yes:
                return

        # Create a temporary file for the new version
        temp_dir = tempfile.gettempdir()
        temp_exe_path = os.path.join(temp_dir, "WorkDayTimer_new.exe")

        # Create progress dialog - non-modal to allow user to continue using the app
        progress_dialog = QDialog(None)
        progress_dialog.setWindowTitle("Downloading Update")
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        progress_dialog.setModal(False)  # Non-modal to allow user interaction with main app
        progress_dialog.resize(300, 120)
        
        layout = QVBoxLayout()
        label = QLabel("Downloading update...")
        layout.addWidget(label)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        layout.addWidget(progress_bar)
        
        # Add cancel button
        cancel_button = QPushButton("Cancel")
        layout.addWidget(cancel_button)
        
        progress_dialog.setLayout(layout)
        progress_dialog.show()
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()  # Ensure dialog is displayed

        # Flag to indicate if download was cancelled
        download_cancelled = False
        
        def cancel_download():
            nonlocal download_cancelled
            download_cancelled = True
            logging.info("Download cancelled by user")
        
        cancel_button.clicked.connect(cancel_download)

        # Download in a separate thread
        download_success = False
        download_error = None
        
        def download_file():
            nonlocal download_success, download_error
            try:
                # Set timeout for the request
                response = requests.get(github_url, stream=True, timeout=30)
                if response.status_code == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(temp_exe_path, "wb") as exe_file:
                        # Create a function to update UI safely
                        def update_ui(progress_value=None, status_text=None, indeterminate=False):
                            def do_update():
                                if indeterminate:
                                    progress_bar.setRange(0, 0)
                                elif progress_value is not None:
                                    progress_bar.setRange(0, 100)
                                    progress_bar.setValue(progress_value)
                                if status_text is not None:
                                    label.setText(status_text)
                            QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                            QApplication.processEvents()
                        
                        if total_size == 0:
                            # If content-length header is missing, set indeterminate progress bar
                            update_ui(indeterminate=True, status_text="Downloading update... (size unknown)")
                        
                        for chunk in response.iter_content(chunk_size=4096):  # Use larger chunk size for faster download
                            if download_cancelled:
                                logging.info("Download cancelled, closing connection")
                                break
                            if chunk:
                                exe_file.write(chunk)
                                downloaded_size += len(chunk)
                                if total_size > 0:
                                    progress = int((downloaded_size / total_size) * 100)
                                    # Update UI in main thread
                                    QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                                    progress_bar.setValue(progress)
                                    label.setText(f"Downloading update... {progress}%")
                                else:
                                    # Update UI even when we don't know the total size
                                    QApplication.postEvent(progress_dialog, QEvent(QEvent.User))
                                    label.setText(f"Downloading update... {downloaded_size} bytes")
                                QApplication.processEvents()
                        
                        if not download_cancelled:
                            download_success = True
                else:
                    download_error = f"Failed to download the update. HTTP Status Code: {response.status_code}"
                    logging.error(download_error)
            except requests.exceptions.Timeout:
                download_error = "Download timed out. Please check your network connection and try again."
                logging.error(download_error)
            except requests.exceptions.RequestException as e:
                download_error = f"Network error: {str(e)}"
                logging.error(download_error)
            except Exception as e:
                download_error = f"An error occurred: {str(e)}"
                logging.error(download_error)
        
        # Start download thread
        download_thread = threading.Thread(target=download_file)
        download_thread.daemon = True
        download_thread.start()
        
        # Create a timer to check download status periodically
        status_check_timer = QTimer(app)
        
        def check_download_status():
            if not download_thread.is_alive():
                status_check_timer.stop()
                progress_dialog.close()
                
                from PyQt5.QtWidgets import QMessageBox
                if download_cancelled:
                    QMessageBox.information(app, "Update Cancelled", "The update download was cancelled.")
                elif download_error:
                    QMessageBox.critical(app, "Update Failed", download_error)
                elif not download_success:
                    QMessageBox.critical(app, "Update Failed", "Download failed for unknown reason.")
                else:
                    # Download completed successfully, proceed with update
                    if not is_running_as_exe:
                        # If running as script, just move the downloaded file to current directory
                        import shutil
                        try:
                            shutil.move(temp_exe_path, local_exe_path)
                            QMessageBox.information(app, "Update Complete", 
                                                  f"Executable downloaded successfully!\n" 
                                                  f"Location: {local_exe_path}\n" 
                                                  f"Run this file to start the application as an executable.")
                        except Exception as e:
                            QMessageBox.critical(app, "Error", f"Failed to move downloaded file: {e}")
                    else:
                        # Create an updater script that will run after this application closes
                        # Place the updater script in the same directory as the executable
                        updater_script = os.path.join(os.path.dirname(local_exe_path), "updater.bat")
                        with open(updater_script, "w") as f:
                            f.write(f"""@echo off
 :: Wait for the old process to fully exit
 timeout /t 3 /nobreak >nul

 :: Kill any remaining instances
 taskkill /f /im WorkDayTimer.exe 2>nul

 :: Wait a bit more to ensure resources are released
 timeout /t 1 /nobreak >nul

 :: Delete the old executable
 del "{local_exe_path}" 2>nul

 :: Move the new executable
 move "{temp_exe_path}" "{local_exe_path}"

 :: Set the PATH to include system and user DLL directories
 set "PATH=%PATH%;C:\Windows\System32;C:\Windows\SysWOW64"

 :: Change to the executable directory
 cd /d "{os.path.dirname(local_exe_path)}"

 :: Clear any PYTHONPATH or other environment variables that might interfere
 set PYTHONPATH=
 set TEMP=%TEMP%
 set TMP=%TMP%

 :: Start the new executable
 start "" "{os.path.basename(local_exe_path)}"

 :: Wait a bit before deleting the script
 timeout /t 1 /nobreak >nul
 del "%~f0"
 """)
                        
                        # Launch the updater script and exit the current application
                        # Set environment variables to help find DLLs
                        env = os.environ.copy()
                        env['PATH'] = env.get('PATH', '') + r';C:\Windows\System32;C:\Windows\SysWOW64'
                        subprocess.Popen(updater_script, shell=True, env=env)
                        app.exit_app()
        
        status_check_timer.timeout.connect(check_download_status)
        status_check_timer.start(100)  # Check every 100ms
    except Exception as e:
        logging.error(f"Update error: {e}")
        if 'progress_dialog' in locals() and progress_dialog:
            progress_dialog.close()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(app, "Update Error", f"An error occurred during the update: {e}")
