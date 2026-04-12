# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['../workday_timer/main.py'],
             pathex=['..'],
             binaries=[],
             datas=[
                 ('../images', 'images'),
                 ('../start_time.txt', '.'),
                 ('../flexible_mode.txt', '.'),
             ],
             hiddenimports=[
                 'xml.parsers.expat',
                 'pkg_resources',
                 'plistlib',
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
              console=False,
              icon='../images/icon.ico',
              disable_windowed_traceback=False,
              target_arch=None,
              codesign_identity=None,
              entitlements_file=None)
