"""テスト共通: フィクスチャを一時ディレクトリへ複製し、CLI を同一プロセスで実行する。"""
from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import tri  # noqa: E402
from trissd.project import Project  # noqa: E402


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


class ProjectCase(unittest.TestCase):
    fixture: str | None = "linkbox"
    use_git = True

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "proj"
        if self.fixture:
            shutil.copytree(FIXTURES / self.fixture, self.root)
        else:
            self.root.mkdir()
        if self.use_git:
            git(self.root, "init", "-q")
            git(self.root, "config", "user.email", "t@example.com")
            git(self.root, "config", "user.name", "t")
            git(self.root, "add", "-A")
            git(self.root, "commit", "-qm", "init", "--allow-empty")

    def tearDown(self):
        self._tmp.cleanup()

    def tri(self, *args: str, stdin: str | None = None) -> tuple[int, str]:
        out = io.StringIO()
        old_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out):
                try:
                    code = tri.main(["--root", str(self.root), *args])
                except SystemExit as e:  # 引数エラー等
                    code = e.code if isinstance(e.code, int) else 2
                    print(e.code)
        finally:
            sys.stdin = old_stdin
        return code, out.getvalue()

    def project(self) -> Project:
        return Project(self.root)

    def write(self, rel: str, text: str):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def edit(self, rel: str, old: str, new: str):
        text = self.read(rel)
        self.assertIn(old, text)
        self.write(rel, text.replace(old, new, 1))
