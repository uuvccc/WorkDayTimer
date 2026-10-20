# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('images', 'images'), ('ascii_animations', 'ascii_animations')],
    hiddenimports=['PyQt5.sip', 'keyboard', 'win32gui', 'win32con'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 本应用为纯 QWidget（QtCore/QtGui/QtWidgets），以下 Qt 模块不使用；
    # PyQt5 的 hook 默认会全量收进包，在此排除以减小体积
    excludes=[
        'PyQt5.QtNetwork', 'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
        'PyQt5.QtSvg', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
        'PyQt5.QtOpenGL', 'PyQt5.QtPrintSupport', 'PyQt5.QtSql', 'PyQt5.QtTest',
        'PyQt5.QtWebChannel', 'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebSockets', 'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns', 'PyQt5.QtBluetooth', 'PyQt5.QtDesigner',
        'PyQt5.QtHelp', 'PyQt5.QtLocation', 'PyQt5.QtNfc', 'PyQt5.QtPositioning',
        'PyQt5.QtRemoteObjects', 'PyQt5.QtSensors', 'PyQt5.QtSerialPort',
        'PyQt5.QtDBus', 'PyQt5.Qt',
    ],
    noarchive=False,
    optimize=0,
)

# ---- 二进制/数据文件过滤：进一步剔除与功能无关的大文件 ----
# 实测（v1.0.0.113 解包）：opengl32sw.dll 7.4MB、Qt5Quick+Qml 2.9MB、
# Qt5Network+OpenSSL 2.5MB，均为未使用组件
_EXCLUDED_BIN_PREFIXES = (
    'opengl32sw',      # 软件 OpenGL 回退库，纯 QWidget 光栅绘制不需要
    'd3dcompiler_',    # ANGLE/D3D 着色器编译器，仅 Quick/Qml/GL 需要
    'libglesv2', 'libegl',  # ANGLE，同上
    'libcrypto', 'libssl',  # OpenSSL，仅 Qt5Network 需要
    'qt5qml', 'qt5quick', 'qt5network', 'qt5svg', 'qt5multimedia',
    'qt5printsupport', 'qt5sql', 'qt5test', 'qt5web', 'qt5xml',
    'qt5bluetooth', 'qt5designer', 'qt5help', 'qt5location', 'qt5nfc',
    'qt5positioning', 'qt5remoteobjects', 'qt5sensors', 'qt5serialport',
)
_EXCLUDED_PLUGIN_DIRS = ('plugins/iconengines/', 'plugins/bearer/')


def _keep_binary(name):
    low = name.replace('\\', '/').lower()
    base = low.rsplit('/', 1)[-1]
    if any(base.startswith(p) for p in _EXCLUDED_BIN_PREFIXES):
        return False
    # 平台插件只保留 Windows 主插件
    if 'plugins/platforms/' in low and base != 'qwindows.dll':
        return False
    if any(part in low for part in _EXCLUDED_PLUGIN_DIRS):
        return False
    return True


a.binaries = [b for b in a.binaries if _keep_binary(b[0])]
# Qt 翻译文件（界面无多语言需求）
a.datas = [d for d in a.datas if '/translations/' not in d[0].replace('\\', '/').lower()]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MiniTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['images\\icon.ico'],
)
