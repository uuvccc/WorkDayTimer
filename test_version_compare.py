#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版本比较功能
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 WorkdayTimer 类
from workday_timer import WorkdayTimer

# 创建一个模拟的 QApplication 对象
class MockApp:
    def postEvent(self, *args, **kwargs):
        pass

# 创建 WorkdayTimer 实例
timer = WorkdayTimer(MockApp())

# 测试版本比较功能
print("测试版本比较功能")
print("=" * 50)

# 测试用例
test_cases = [
    ("1.0.0", "1.0.0", False, "相同版本"),
    ("1.0.1", "1.0.0", True, "小版本更新"),
    ("1.1.0", "1.0.0", True, "中版本更新"),
    ("2.0.0", "1.0.0", True, "大版本更新"),
    ("0.9.9", "1.0.0", False, "旧版本"),
    ("1.0.0.1", "1.0.0", True, "补丁版本更新"),
    ("1.0", "1.0.0", False, "版本号长度不同"),
]

# 运行测试
passed = 0
failed = 0

for latest, current, expected, description in test_cases:
    result = timer._is_newer_version(latest, current)
    status = "✅" if result == expected else "❌"
    print(f"{status} {description}: {current} -> {latest} (期望: {expected}, 实际: {result})")
    if result == expected:
        passed += 1
    else:
        failed += 1

print("\n测试结果:")
print(f"通过: {passed}")
print(f"失败: {failed}")

if failed == 0:
    print("\n🎉 所有测试通过！版本比较功能正常工作。")
else:
    print("\n❌ 有测试失败，版本比较功能可能存在问题。")
