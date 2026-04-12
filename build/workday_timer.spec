# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# 确保使用正确的Python版本
sys.setrecursionlimit(5000)

# 计算项目根目录（spec文件所在目录的父目录）
spec_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(spec_dir)

block_cipher = None

# 应用程序配置
a = Analysis([os.path.join(root_dir, 'workday_timer', 'main.py')],
             pathex=[root_dir],
             binaries=[],
             datas=[
                 (os.path.join(root_dir, 'images'), 'images'),
                 (os.path.join(root_dir, 'start_time.txt'), '.'),
                 (os.path.join(root_dir, 'flexible_mode.txt'), '.'),
             ],
             hiddenimports=[
                 'xml.parsers.expat',
                 'pkg_resources',
                 'plistlib',
             ],
             hookspath=[os.path.join(root_dir, 'hooks')],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件配置
executable = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name='WorkDayTimer',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              upx_exclude=[],
              runtime_tmpdir=None,
              console=False,  # 无控制台窗口
              icon=os.path.join(root_dir, 'images', 'icon.ico'),
              disable_windowed_traceback=False,
              target_arch=None,
              codesign_identity=None,
              entitlements_file=None)

# 构建目录配置
coll = COLLECT(executable,
             a.binaries,
             a.zipfiles,
             a.datas,
             strip=False,
             upx=True,
             upx_exclude=[],
             name='WorkDayTimer')
