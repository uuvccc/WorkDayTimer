"""Nuitka standalone 构建脚本：编译 + 打包成发布 zip。

本项目打包工具已从 PyInstaller 切换为 Nuitka standalone 模式：
- standalone 模式下 exe 与所有依赖/资源同目录，不再解压到临时目录；
- 发布产物为一个 zip 包，解压即可运行；
- 更新时下载 zip 覆盖应用目录（保留用户配置/自定义资源）。

构建入口：python build.py
产物：dist/MiniTools.zip

注意：构建参数统一在此脚本维护，CI 与本地共用同一入口，避免双份漂移。
"""
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
# Nuitka standalone 默认输出目录为 <入口名>.dist（main.py → main.dist）
BUILD_DIR = os.path.join(DIST, "main.dist")
ZIP_PATH = os.path.join(DIST, "MiniTools.zip")
# 增量更新元数据：客户端据此判断本地哪些文件需要更新
MANIFEST_PATH = os.path.join(DIST, "MiniTools.manifest.json")
# 逐文件压缩资产目录（每个文件一个 .gz，供增量下载）
ASSETS_DIR = os.path.join(DIST, "assets")

# 本应用只使用 PyQt5 的 QtCore/QtGui/QtWidgets，以下 Qt 模块不需要，
# 显式 nofollow 可减少 Nuitka 的依赖收集范围。
NOFOLLOW_QT_MODULES = [
    "PyQt5.QtNetwork", "PyQt5.QtQml", "PyQt5.QtQuick", "PyQt5.QtQuickWidgets",
    "PyQt5.QtSvg", "PyQt5.QtMultimedia", "PyQt5.QtMultimediaWidgets",
    "PyQt5.QtOpenGL", "PyQt5.QtPrintSupport", "PyQt5.QtSql", "PyQt5.QtTest",
    "PyQt5.QtWebChannel", "PyQt5.QtWebEngine", "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebEngineWidgets", "PyQt5.QtWebSockets", "PyQt5.QtXml",
    "PyQt5.QtXmlPatterns", "PyQt5.QtBluetooth", "PyQt5.QtDesigner",
    "PyQt5.QtHelp", "PyQt5.QtLocation", "PyQt5.QtNfc", "PyQt5.QtPositioning",
    "PyQt5.QtRemoteObjects", "PyQt5.QtSensors", "PyQt5.QtSerialPort",
    "PyQt5.QtDBus",
]


# 本应用未使用、且删掉对应 DLL 后必然加载失败的 Qt 插件。
# PyQt5 下 --include-qt-plugins 未完全生效（Nuitka 对 obsolete PyQt5 支持不完整），
# 因此插件裁剪统一放在构建后处理，避免出现"插件在、依赖 DLL 没了"的坏引用。
UNUSED_QT_PLUGINS = [
    "iconengines/qsvgicon.dll",                   # 依赖已移除的 qt5svg.dll
    "imageformats/qsvg.dll",                      # 依赖已移除的 qt5svg.dll
    "mediaservice/dsengine.dll",                  # 依赖已移除的 qt5multimedia.dll
    "mediaservice/qtmedia_audioengine.dll",       # 同上
    "mediaservice/wmfengine.dll",                 # 同上
    "printsupport/windowsprintersupport.dll",     # 依赖已移除的 qt5printsupport.dll
    "platforms/qwebgl.dll",                       # 需要 OpenGL/Quick，纯 QWidget 不用
    "platforms/qminimal.dll",                     # 非 Windows 平台插件，无用
    "platforms/qoffscreen.dll",                   # 同上
    "platformthemes/qxdgdesktopportal.dll",       # Linux 桌面主题插件
]


def run_nuitka():
    """调用 Nuitka 以 standalone 模式编译 main.py。"""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        # 无控制台窗口（GUI 应用）
        "--windows-console-mode=disable",
        # 应用图标
        "--windows-icon-from-ico=images/icon.ico",
        # 资源目录：源目录=目标目录（exe 旁边）
        "--include-data-dir=images=images",
        "--include-data-dir=ascii_animations=ascii_animations",
        # PyQt5 插件自动处理 Qt 依赖与插件
        "--enable-plugin=pyqt5",
        # 只收集纯 QWidget 应用必需的 Qt 插件（PyQt5 下该参数仅部分生效，
        # 残留插件由 clean_unused_build_files 兜底清理）
        "--include-qt-plugins=platforms,styles,imageformats",
        # 输出文件名与目录
        "--output-filename=MiniTools.exe",
        "--output-dir=dist",
        # 依赖（如 C 编译器、依赖包）缺失时自动下载安装
        "--assume-yes-for-downloads",
        # 编译完成后移除中间构建目录（.build）
        "--remove-output",
    ]
    for mod in NOFOLLOW_QT_MODULES:
        cmd.append(f"--nofollow-import-to={mod}")
    cmd.append("main.py")

    print("[build] Running:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def clean_unused_build_files():
    """删除 Nuitka PyQt5 插件自动收集但本应用未使用的 DLL 与 Qt 插件。

    本应用为纯 QWidget 应用（只用 QtCore/QtGui/QtWidgets），以下 DLL 未被使用：
    - qt5quick/qml/qmlmodels: QML/Quick 渲染，纯 QWidget 不需要
    - qt5network: 网络模块未使用（HTTP 走 requests）
    - qt5multimedia: 多媒体未使用
    - qt5svg: SVG 支持未使用（图片均为 PNG/ICO）
    - qt5printsupport: 打印支持未使用
    - qt5websockets: WebSocket 未使用
    - qt5dbus: D-Bus 未使用（Windows 桌面应用）
    - libcrypto/libssl/ssleay32: OpenSSL，仅 qt5network 需要
    """
    unused_dlls = [
        "qt5quick.dll", "qt5qml.dll", "qt5qmlmodels.dll",
        "qt5network.dll", "qt5multimedia.dll", "qt5svg.dll",
        "qt5printsupport.dll", "qt5websockets.dll", "qt5dbus.dll",
        "libcrypto-3.dll", "libeay32.dll", "libssl-3.dll", "ssleay32.dll",
    ]
    removed = 0
    for dll in unused_dlls:
        path = os.path.join(BUILD_DIR, dll)
        if os.path.exists(path):
            os.remove(path)
            removed += 1
            print(f"[build] Removed unused DLL: {dll}")

    plugins_root = os.path.join(BUILD_DIR, "PyQt5", "qt-plugins")
    for plugin in UNUSED_QT_PLUGINS:
        path = os.path.join(plugins_root, *plugin.split("/"))
        if os.path.exists(path):
            os.remove(path)
            removed += 1
            print(f"[build] Removed unused Qt plugin: {plugin}")

    print(f"[build] Removed {removed} unused file(s)")


def make_zip():
    """把 main.dist/ 目录打包成 MiniTools.zip（zip 内不嵌套目录）。"""
    print(f"[build] Creating zip: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(BUILD_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, BUILD_DIR)
                zf.write(full, arc)
    size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
    print(f"[build] Done: {ZIP_PATH} ({size_mb:.2f} MB)")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _asset_name(rel_path):
    """把相对路径扁平化为 release 资产名（GitHub 资产名不允许包含 /）。"""
    return rel_path.replace("\\", "/").replace("/", "__") + ".gz"


def _current_version():
    """从 app/__init__.py 读取版本号（不 import app，避免副作用）。"""
    try:
        with open(os.path.join(ROOT, "app", "__init__.py"), encoding="utf-8") as f:
            m = re.search(r"""__version__\s*=\s*['"]([^'"]+)""", f.read())
            return m.group(1) if m else "unknown"
    except OSError:
        return "unknown"


def make_manifest_and_assets():
    """生成增量更新元数据：manifest.json + 逐文件 .gz 资产。

    manifest 记录每个文件相对路径、大小与 sha256；客户端比对本机文件后
    只下载有差异的那几个 .gz，避免每次更新都拉完整的 20+ MB zip。
    """
    if os.path.exists(ASSETS_DIR):
        shutil.rmtree(ASSETS_DIR)
    os.makedirs(ASSETS_DIR, exist_ok=True)

    files = []
    for root, _dirs, names in os.walk(BUILD_DIR):
        for name in names:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, BUILD_DIR).replace("\\", "/")
            asset = _asset_name(rel)
            # mtime=0 让相同内容产出相同字节，便于比对与缓存
            with open(full, "rb") as src, gzip.GzipFile(
                os.path.join(ASSETS_DIR, asset), "wb", compresslevel=9, mtime=0
            ) as dst:
                shutil.copyfileobj(src, dst)
            files.append({
                "path": rel,
                "asset": asset,
                "size": os.path.getsize(full),
                "sha256": _sha256_file(full),
            })

    manifest = {
        "version": _current_version(),
        "files": sorted(files, key=lambda entry: entry["path"]),
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    raw_mb = sum(entry["size"] for entry in files) / 1024 / 1024
    asset_mb = sum(
        os.path.getsize(os.path.join(ASSETS_DIR, entry["asset"])) for entry in files
    ) / 1024 / 1024
    print(f"[build] Manifest: {MANIFEST_PATH} ({len(files)} files, {raw_mb:.2f} MB raw)")
    print(f"[build] Assets: {ASSETS_DIR} ({asset_mb:.2f} MB compressed)")


def main():
    # 清理旧产物，保证增量构建不残留旧文件
    for path in (BUILD_DIR, os.path.join(DIST, "main.build"), ASSETS_DIR):
        if os.path.exists(path):
            shutil.rmtree(path)
    for path in (ZIP_PATH, MANIFEST_PATH):
        if os.path.exists(path):
            os.remove(path)

    run_nuitka()
    clean_unused_build_files()
    make_zip()
    make_manifest_and_assets()


if __name__ == "__main__":
    main()
