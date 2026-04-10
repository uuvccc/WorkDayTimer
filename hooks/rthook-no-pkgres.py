# 自定义运行时钩子，避免导入 pkg_resources
import sys

# 跳过 pkg_resources 的导入
sys.modules['pkg_resources'] = type('MockPkgResources', (), {
    'DistributionNotFound': Exception,
    'VersionConflict': Exception,
})()
