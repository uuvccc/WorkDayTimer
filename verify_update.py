#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证更新功能
"""

import sys
import os
import requests

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 setup 模块以获取当前版本
import setup

def check_github_release():
    """检查 GitHub 上的最新版本"""
    try:
        # 获取当前版本
        current_version = setup.setup.version
        print(f"当前版本: {current_version}")
        
        # 检查 GitHub 上的最新版本
        api_url = "https://api.github.com/repos/uuvccc/WorkDayTimer/releases/latest"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            release_data = response.json()
            latest_version = release_data['tag_name'].lstrip('v')
            print(f"GitHub 最新版本: {latest_version}")
            
            # 比较版本
            def is_newer_version(latest, current):
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
            
            if is_newer_version(latest_version, current_version):
                print("✅ 发现新版本！")
                print(f"📦 新版本: {latest_version}")
                print(f"🔗 下载链接: {release_data['html_url']}")
            else:
                print("✅ 当前已是最新版本")
        else:
            print(f"❌ 无法连接到 GitHub API: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查更新时出错: {e}")

def check_download_url():
    """检查下载链接是否有效"""
    try:
        download_url = "https://github.com/uuvccc/WorkDayTimer/releases/latest/download/WorkDayTimer.exe"
        print(f"\n检查下载链接: {download_url}")
        
        # 发送 HEAD 请求以检查链接是否有效
        response = requests.head(download_url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ 下载链接有效")
            if 'content-length' in response.headers:
                file_size = int(response.headers['content-length'])
                print(f"📁 文件大小: {file_size / (1024 * 1024):.2f} MB")
        else:
            print(f"❌ 下载链接无效: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查下载链接时出错: {e}")

if __name__ == '__main__':
    print("🔍 验证 WorkDayTimer 更新功能")
    print("=" * 50)
    
    check_github_release()
    check_download_url()
    
    print("\n✅ 更新功能验证完成！")
