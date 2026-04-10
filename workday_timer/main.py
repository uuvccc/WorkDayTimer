#!/usr/bin/env python3

import sys
import logging
import os

# 最优先模拟所有可能导致 pyexpat 错误的模块
# 这将在 PyInstaller 的运行时钩子执行前生效
class MockModule:
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

# 模拟 xml 模块及其子模块
sys.modules['xml'] = MockModule()
sys.modules['xml.parsers'] = MockModule()
sys.modules['xml.parsers.expat'] = MockModule()

# 模拟 plistlib 模块
sys.modules['plistlib'] = MockModule()

# 模拟 pkg_resources 模块
sys.modules['pkg_resources'] = MockModule()
sys.modules['pkg_resources'].DistributionNotFound = Exception
sys.modules['pkg_resources'].VersionConflict = Exception
sys.modules['pkg_resources'].get_distribution = lambda dist: MockModule()
sys.modules['pkg_resources'].get_distribution.version = lambda: '1.0.0'

# 现在导入其他模块
from PyQt5.QtWidgets import QApplication

from workday_timer.config import config
from workday_timer.core.timer import WorkdayTimer
from workday_timer.utils.logger import setup_logging
from workday_timer.utils.error_handler import handle_exception


def main():
    """主函数，启动应用程序"""
    try:
        # 配置日志
        setup_logging()
        
        # 设置全局异常处理
        sys.excepthook = handle_exception
        
        # 创建应用程序实例
        app = QApplication(sys.argv)
        
        # 创建工作计时器实例
        workday_timer = WorkdayTimer(app)
        
        # 运行应用程序
        sys.exit(app.exec_())
    except Exception as e:
        error_message = f"An error occurred: {e}"
        print(error_message)
        logging.error(error_message)
        
        # 创建一个简单的托盘图标用于错误报告
        try:
            app = QApplication(sys.argv)
            from workday_timer.gui.tray import create_error_tray
            create_error_tray(app, str(e))
            sys.exit(app.exec_())
        except:
            pass


if __name__ == '__main__':
    main()
