from PyInstaller.utils.hooks import collect_dynamic_libs

# 收集 pyexpat 的动态库
binaries = collect_dynamic_libs('xml.parsers.expat')
