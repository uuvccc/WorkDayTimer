"""增量更新逻辑测试：文件差异判定与 sha256 计算。

不涉及网络：只验证「哪些本地文件需要重新下载」这一核心判定，
它是增量更新正确性的关键（判错会导致该更新的没更新，或重复下载）。
"""
import hashlib
import importlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from app.services.update_service import _select_files_to_fetch, _sha256_file

# 注意：app.services 包的 __init__ 里导出了同名单例，直接
# `from app.services import update_service` 拿到的是单例而不是模块，
# 需要拿到模块本身才能 patch 模块级的 _is_packaged。
update_service_module = importlib.import_module("app.services.update_service")
update_service = update_service_module.update_service


class TestSha256File(unittest.TestCase):
    def test_matches_hashlib(self):
        payload = b"MiniTools" * 1000
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.bin")
            with open(path, "wb") as f:
                f.write(payload)
            self.assertEqual(_sha256_file(path), hashlib.sha256(payload).hexdigest())


class TestSelectFilesToFetch(unittest.TestCase):
    def _write(self, root, rel_path, payload):
        path = os.path.join(root, *rel_path.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(payload)
        return path

    @staticmethod
    def _entry(rel_path, payload):
        return {
            "path": rel_path,
            "asset": rel_path.replace("/", "__") + ".gz",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    def test_missing_file_needs_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [self._entry("MiniTools.exe", b"new")]
            self.assertEqual(_select_files_to_fetch(entries, tmp), entries)

    def test_identical_file_skipped(self):
        payload = b"unchanged"
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "qt5core.dll", payload)
            self.assertEqual(_select_files_to_fetch([self._entry("qt5core.dll", payload)], tmp), [])

    def test_size_mismatch_needs_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "qt5core.dll", b"old")
            entries = [self._entry("qt5core.dll", b"new-version")]
            self.assertEqual(_select_files_to_fetch(entries, tmp), entries)

    def test_same_size_different_content_needs_fetch(self):
        """大小相同但内容不同时必须重下（只比大小会漏判）。"""
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "qt5core.dll", b"AAAA")
            entries = [self._entry("qt5core.dll", b"BBBB")]
            self.assertEqual(_select_files_to_fetch(entries, tmp), entries)

    def test_nested_path_resolved(self):
        payload = b"icon"
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "images/icon.png", payload)
            self.assertEqual(
                _select_files_to_fetch([self._entry("images/icon.png", payload)], tmp), []
            )

    def test_entry_without_path_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_select_files_to_fetch([{"size": 1}], tmp), [])

    def test_mixed_manifest_returns_only_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "a.dll", b"same")
            self._write(tmp, "b.dll", b"old")
            entries = [
                self._entry("a.dll", b"same"),
                self._entry("b.dll", b"new"),
                self._entry("c.dll", b"missing-locally"),
            ]
            result = _select_files_to_fetch(entries, tmp)
            self.assertEqual([e["path"] for e in result], ["b.dll", "c.dll"])


class TestLocalExePath(unittest.TestCase):
    """Nuitka 打包后 sys.executable 是假的 python.exe，更新目标必须取 argv[0]。"""

    def test_prefers_real_exe_from_argv0(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_exe = os.path.join(tmp, "MiniTools.exe")
            open(fake_exe, "wb").close()
            with patch.object(sys, "argv", [fake_exe]):
                self.assertEqual(update_service.get_local_exe_path(), os.path.abspath(fake_exe))

    def test_falls_back_to_sys_executable_without_exe_argv0(self):
        with patch.object(sys, "argv", ["main.py"]):
            self.assertEqual(update_service.get_local_exe_path(), sys.executable)


class TestPrepareUpdaterScript(unittest.TestCase):
    def _make_exe(self, tmp):
        exe = os.path.join(tmp, "MiniTools.exe")
        open(exe, "wb").close()
        return exe

    def test_skipped_when_not_packaged(self):
        """源码运行时不生成更新脚本（否则会把 Python 安装目录当更新目标）。"""
        with tempfile.TemporaryDirectory() as tmp:
            exe = self._make_exe(tmp)
            with patch.object(update_service_module, "_is_packaged", return_value=False):
                self.assertIsNone(update_service.prepare_updater_script(tmp, exe))

    def test_rejects_non_exe_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(update_service_module, "_is_packaged", return_value=True):
                self.assertIsNone(update_service.prepare_updater_script(tmp, "python.exe"))

    def test_script_restarts_real_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = self._make_exe(tmp)
            staging = os.path.join(tmp, "staging")
            os.makedirs(staging)
            with patch.object(update_service_module, "_is_packaged", return_value=True):
                script = update_service.prepare_updater_script(staging, exe)
            self.assertTrue(script)
            with open(script, encoding="utf-8") as f:
                content = f.read()
            self.assertIn('taskkill /f /im "MiniTools.exe"', content)
            self.assertIn(f'start "" /D "{tmp}" "MiniTools.exe"', content)
            self.assertNotIn("python.exe", content.lower())


if __name__ == "__main__":
    unittest.main()
