#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试更新功能，包括版本比较和更新下载
"""

import sys
import os
import unittest
import tempfile
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入需要测试的类
from workday_timer import WorkdayTimer

class TestUpdateFunctionalityFull(unittest.TestCase):
    """完整测试更新功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建一个模拟的 QApplication 对象
        self.mock_app = Mock()
        # 创建 WorkdayTimer 实例
        self.timer = WorkdayTimer(self.mock_app)
    
    def test_version_comparison(self):
        """测试版本比较功能"""
        # 测试相同版本
        self.assertFalse(self.timer._is_newer_version("1.0.0", "1.0.0"))
        
        # 测试新版本
        self.assertTrue(self.timer._is_newer_version("1.0.1", "1.0.0"))
        self.assertTrue(self.timer._is_newer_version("1.1.0", "1.0.0"))
        self.assertTrue(self.timer._is_newer_version("2.0.0", "1.0.0"))
        
        # 测试旧版本
        self.assertFalse(self.timer._is_newer_version("0.9.9", "1.0.0"))
        
        # 测试不同长度的版本号
        self.assertTrue(self.timer._is_newer_version("1.0.0.1", "1.0.0"))
        self.assertFalse(self.timer._is_newer_version("1.0", "1.0.0"))
    
    @patch('workday_timer.requests.get')
    @patch('workday_timer.setup')
    def test_check_for_updates_no_update(self, mock_setup, mock_get):
        """测试检查更新功能 - 无更新"""
        # 模拟 setup.py 中的版本
        mock_setup.setup.version = "1.0.0"
        
        # 模拟 GitHub API 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tag_name': 'v1.0.0'  # 相同版本
        }
        mock_get.return_value = mock_response
        
        # 模拟 QApplication.postEvent
        with patch.object(self.timer.app, 'postEvent') as mock_post_event:
            # 调用检查更新方法
            self.timer.check_for_updates()
            # 验证 postEvent 没有被调用（因为版本相同）
            mock_post_event.assert_not_called()
    
    @patch('workday_timer.requests.get')
    @patch('workday_timer.setup')
    def test_check_for_updates_with_update(self, mock_setup, mock_get):
        """测试检查更新功能 - 有更新"""
        # 模拟 setup.py 中的版本
        mock_setup.setup.version = "1.0.0"
        
        # 模拟 GitHub API 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tag_name': 'v1.0.1'  # 新版本
        }
        mock_get.return_value = mock_response
        
        # 模拟 QApplication.postEvent
        with patch.object(self.timer.app, 'postEvent') as mock_post_event:
            # 调用检查更新方法
            self.timer.check_for_updates()
            # 验证 postEvent 被调用（因为有新版本）
            mock_post_event.assert_called_once()
    
    @patch('workday_timer.requests.get')
    def test_check_for_updates_api_error(self, mock_get):
        """测试检查更新功能 - API 错误"""
        # 模拟 GitHub API 响应 - 网络错误
        mock_get.side_effect = Exception("Network error")
        
        # 调用检查更新方法，应该不会崩溃
        try:
            self.timer.check_for_updates()
        except Exception as e:
            self.fail(f"check_for_updates() raised {type(e).__name__} unexpectedly!")
    
    @patch('workday_timer.requests.get')
    @patch('workday_timer.os.path.exists')
    @patch('workday_timer.QMessageBox')
    @patch('workday_timer.tempfile.gettempdir')
    @patch('workday_timer.os.path.join')
    @patch('workday_timer.open')
    @patch('workday_timer.threading.Thread')
    @patch('workday_timer.QTimer')
    def test_update_application_as_script(self, mock_qtimer, mock_thread, mock_open, mock_join, mock_gettempdir, mock_messagebox, mock_exists, mock_get):
        """测试以脚本方式运行时的更新功能"""
        # 模拟运行方式为脚本
        with patch('workday_timer.sys.argv', ['workday_timer.py']):
            with patch('workday_timer.os.getcwd', return_value='C:\\test'):
                # 模拟 QMessageBox.question 返回 Yes
                mock_messagebox.question.return_value = Mock()
                mock_messagebox.question.return_value.__eq__.return_value = True
                
                # 模拟临时目录
                mock_gettempdir.return_value = 'C:\\temp'
                
                # 模拟路径连接
                mock_join.side_effect = lambda *args: '\\'.join(args)
                
                # 模拟文件打开
                mock_file = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                # 模拟线程
                mock_thread_instance = Mock()
                mock_thread.return_value = mock_thread_instance
                
                # 模拟 QTimer
                mock_timer_instance = Mock()
                mock_qtimer.return_value = mock_timer_instance
                
                # 模拟下载响应
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers.get.return_value = '1024'
                mock_response.iter_content.return_value = [b'fake data']
                mock_get.return_value = mock_response
                
                # 模拟 shutil.move
                with patch('workday_timer.shutil.move') as mock_move:
                    # 调用更新方法
                    self.timer.update_application()
                    
                    # 验证消息框被调用
                    mock_messagebox.question.assert_called()
                    # 验证线程被启动
                    mock_thread_instance.start.assert_called()
                    # 验证定时器被启动
                    mock_timer_instance.start.assert_called()
    
    @patch('workday_timer.requests.get')
    @patch('workday_timer.os.path.exists')
    @patch('workday_timer.tempfile.gettempdir')
    @patch('workday_timer.os.path.join')
    @patch('workday_timer.open')
    @patch('workday_timer.threading.Thread')
    @patch('workday_timer.QTimer')
    @patch('workday_timer.subprocess.Popen')
    def test_update_application_as_exe(self, mock_popen, mock_qtimer, mock_thread, mock_open, mock_join, mock_gettempdir, mock_exists, mock_get):
        """测试以可执行文件方式运行时的更新功能"""
        # 模拟运行方式为可执行文件
        with patch('workday_timer.sys.argv', ['WorkDayTimer.exe']):
            # 模拟临时目录
            mock_gettempdir.return_value = 'C:\\temp'
            
            # 模拟路径连接
            mock_join.side_effect = lambda *args: '\\'.join(args)
            
            # 模拟文件打开
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # 模拟线程
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            # 模拟 QTimer
            mock_timer_instance = Mock()
            mock_qtimer.return_value = mock_timer_instance
            
            # 模拟下载响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers.get.return_value = '1024'
            mock_response.iter_content.return_value = [b'fake data']
            mock_get.return_value = mock_response
            
            # 调用更新方法
            self.timer.update_application()
            
            # 验证线程被启动
            mock_thread_instance.start.assert_called()
            # 验证定时器被启动
            mock_timer_instance.start.assert_called()

if __name__ == '__main__':
    unittest.main()
