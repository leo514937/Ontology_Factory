from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = [str(ROOT / "src")]
if os.environ.get("PYTHONPATH"):
    PYTHONPATH.append(os.environ["PYTHONPATH"])
ENV = os.environ | {"PYTHONPATH": os.pathsep.join(PYTHONPATH)}


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wikimg", *args],
        cwd=cwd,
        env=ENV,
        text=True,
        capture_output=True,
        check=False,
    )


class WikiCliTests(unittest.TestCase):
    @unittest.skipIf(sys.version_info[:2] < (3, 10), "wikimg requires Python 3.10+")
    def test_full_document_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_cli("init", cwd=workspace)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((workspace / ".wikimg" / "config.json").exists())
            self.assertTrue((workspace / "wiki" / "common").exists())
            self.assertTrue((workspace / "wiki" / "domain").exists())
            self.assertTrue((workspace / "wiki" / "private").exists())

            result = run_cli("new", "common", "Getting Started", cwd=workspace)
            self.assertEqual(result.returncode, 0, result.stdout)
            document_path = workspace / "wiki" / "common" / "getting-started.md"
            self.assertTrue(document_path.exists())

            result = run_cli("list", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            self.assertIn("common:getting-started", result.stdout)

            result = run_cli("show", "common:getting-started", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            self.assertIn("# Getting Started", result.stdout)

            result = run_cli(
                "rename",
                "common:getting-started",
                "Architecture Notes",
                cwd=workspace,
            )
            self.assertEqual(result.returncode, 0)
            renamed_path = workspace / "wiki" / "common" / "architecture-notes.md"
            self.assertTrue(renamed_path.exists())
            self.assertIn("# Architecture Notes", renamed_path.read_text(encoding="utf-8"))

            result = run_cli("move", "common:architecture-notes", "private", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            moved_path = workspace / "wiki" / "private" / "architecture-notes.md"
            self.assertTrue(moved_path.exists())

            moved_path.write_text(
                "# Architecture Notes\n\nThis is a private note.\n",
                encoding="utf-8",
            )
            result = run_cli("search", "private note", "--content", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            self.assertIn("private:architecture-notes", result.stdout)

            result = run_cli("doctor", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Workspace looks healthy.", result.stdout)

            result = run_cli("delete", "private:architecture-notes", "--yes", cwd=workspace)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(moved_path.exists())

    @unittest.skipIf(sys.version_info[:2] < (3, 10), "wikimg requires Python 3.10+")
    def test_explicit_root_uses_exact_workspace_instead_of_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            child = parent / "nested"
            child.mkdir()

            result = run_cli("init", cwd=parent)
            self.assertEqual(result.returncode, 0, result.stderr)

            result = run_cli("--root", str(child), "new", "domain", "Child Topic", cwd=parent)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((child / ".wikimg" / "config.json").exists())
            self.assertTrue((child / "wiki" / "domain" / "child-topic.md").exists())
            self.assertFalse((parent / "wiki" / "domain" / "child-topic.md").exists())


if __name__ == "__main__":
    unittest.main()
