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


class IntelArchiveFilterTests(unittest.TestCase):
    def _write_job(self, path: Path, company: str, position: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "\n".join(
                [
                    "---",
                    "type: qiuzhao-intel-job",
                    f"公司: {company}",
                    f"岗位: {position}",
                    "---",
                    f"# {company}-{position}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_list_intel_skips_mismatch_archive_even_when_include_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            intel = root / "秋招" / "02_情报库"
            self._write_job(intel / "光轮智能" / "光轮-Agent.md", "光轮智能", "Agent")
            self._write_job(
                intel / "_归档" / "帆软" / "帆软-Agent.md",
                "帆软",
                "已截止Agent",
            )
            self._write_job(
                intel / "_archived_具身智能" / "诺因智能" / "诺因-具身.md",
                "诺因智能",
                "具身智能 Agent",
            )
            active = vio.list_intel(root)
            closed = vio.list_intel(root, include_archived=True)
            stems_active = {c.stem for c in active}
            stems_closed = {c.stem for c in closed}
            self.assertEqual(stems_active, {"光轮-Agent"})
            self.assertEqual(stems_closed, {"光轮-Agent", "帆软-Agent"})
            self.assertNotIn("诺因-具身", stems_closed)

    def test_archive_mismatch_job_leaves_sibling_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            intel = root / "秋招" / "02_情报库"
            self._write_job(
                intel / "智元机器人" / "智元-灵犀.md",
                "智元机器人",
                "Agent算法工程师",
            )
            self._write_job(
                intel / "智元机器人" / "智元-具身.md",
                "智元机器人",
                "具身 Agent 算法研究员",
            )
            dest = vio.archive_mismatch_job("智元-具身", root=root)
            self.assertTrue(dest.exists())
            self.assertIn("_archived_具身智能", dest.parts)
            stems = {c.stem for c in vio.list_intel(root)}
            self.assertEqual(stems, {"智元-灵犀"})
            self.assertTrue((intel / "智元机器人" / "智元-灵犀.md").is_file())


if __name__ == "__main__":
    unittest.main()