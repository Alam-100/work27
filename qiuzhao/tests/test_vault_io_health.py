from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import vault_io as vio


class VaultPathAndHealthTests(unittest.TestCase):
    def test_vault_root_uses_safe_default_when_env_is_absent(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(vio.vault_root(), vio.DEFAULT_VAULT)

    def test_missing_vault_does_not_create_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "missing-vault"
            report = vio.health_check(root, light=True)

            self.assertFalse(report.qiuzhao_ok)
            self.assertEqual(report.pending_jobs, 0)
            self.assertFalse(root.exists())
            self.assertIn("找不到秋招目录", report.messages[0])

    def test_unreadable_vault_returns_health_failure(self) -> None:
        broken = mock.Mock()
        broken.is_dir.side_effect = OSError(1392, "文件或目录损坏且无法读取")
        broken.__str__ = mock.Mock(return_value="E:\\obsidian\\My_docs\\秋招")

        with mock.patch.object(vio, "qiuzhao_root", return_value=broken):
            report = vio.health_check(Path("E:/obsidian/My_docs"), light=True)

        self.assertFalse(report.qiuzhao_ok)
        self.assertEqual(report.pending_jobs, 0)
        self.assertIn("无法访问秋招目录", report.messages[0])

    def test_list_typed_treats_unreadable_directory_as_empty(self) -> None:
        broken = mock.Mock()
        broken.is_dir.side_effect = OSError(1392, "文件或目录损坏且无法读取")

        self.assertEqual(vio._list_typed(broken, "qiuzhao-intel-job"), [])


if __name__ == "__main__":
    unittest.main()