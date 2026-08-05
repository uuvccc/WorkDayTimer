import os
import sys
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from app.utils.image import transparent_icon

from app.main_window import MainWindow
from app.config.constants import ICON_FILE
from app.utils.logger import logger

class MiniToolsApplication:
    APP_NAME = "MiniTools"

    def __init__(self):
        self.app = None
        self.main_window = None

    def _setup_exception_handler(self):
        def handle_exception(exc_type, exc_value, exc_traceback):
            import traceback
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            logger.error("Uncaught exception:\n%s", error_msg)

            try:
                QMessageBox.critical(None, "Error", f"An error occurred:\n{str(exc_value)}")
            except Exception:
                pass

        sys.excepthook = handle_exception

    def run(self):
        try:
            # 确保工作目录是应用所在目录（自启时 Windows 可能以 System32 为 CWD）
            exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(sys.argv[0]))
            os.chdir(exe_dir)
            logger.info(f"Application starting | working_dir={exe_dir} | frozen={getattr(sys, 'frozen', False)}")

            import traceback
            self._setup_exception_handler()
            logger.debug("Exception handler installed")

            self.app = QApplication(sys.argv)
            self.app.setQuitOnLastWindowClosed(False)
            logger.debug("QApplication created")

            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.APP_NAME)
                logger.debug("Windows AppUserModelID set")

            if ICON_FILE and __import__('os').path.exists(ICON_FILE):
                self.app.setWindowIcon(transparent_icon(ICON_FILE))
                logger.debug(f"Window icon set: {ICON_FILE}")
            else:
                logger.warning(f"Window icon not found: {ICON_FILE}")

            self.main_window = MainWindow(self.app)
            logger.info("MainWindow created successfully, entering event loop")

            return sys.exit(self.app.exec_())

        except Exception as e:
            error_message = f"Fatal error during startup: {e}"
            print(error_message)
            logger.error(error_message, exc_info=True)

            try:
                self.app = QApplication(sys.argv)
                from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction

                tray_icon = QSystemTrayIcon()
                if ICON_FILE and __import__('os').path.exists(ICON_FILE):
                    tray_icon.setIcon(transparent_icon(ICON_FILE))

                menu = QMenu()
                exit_action = QAction("Exit", None)
                exit_action.triggered.connect(self.app.quit)
                menu.addAction(exit_action)
                tray_icon.setContextMenu(menu)
                tray_icon.show()
                tray_icon.showMessage(f"{self.APP_NAME} Error", f"An error occurred: {e}",
                                      QSystemTrayIcon.Critical, 5000)

                return sys.exit(self.app.exec_())
            except:
                return 1

def main():
    application = MiniToolsApplication()
    return application.run()

if __name__ == '__main__':
    main()