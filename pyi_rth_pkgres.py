# 自定义运行时钩子，避免导入 pkg_resources
# 这个文件会替换 PyInstaller 的默认 pyi_rth_pkgres.py

import sys

# 跳过 pkg_resources 的导入
sys.modules['pkg_resources'] = type('MockPkgResources', (), {
    'DistributionNotFound': Exception,
    'VersionConflict': Exception,
})()

# 模拟 pkg_resources.get_distribution 函数
def get_distribution(dist_name):
    class MockDistribution:
        def version(self):
            return '1.0.0'
    return MockDistribution()

sys.modules['pkg_resources'].get_distribution = get_distribution
