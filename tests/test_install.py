"""導入: 一時フォルダへ導入した起動スクリプトから CLI が動き、Skill の写しが Agent Skills の形でそろう。"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import install  # noqa: E402

SKILL_NAMES = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class InstallTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.prefix, self.bin = self.base / "prefix", self.base / "bin"
        self.agents, self.claude = self.base / "agents-skills", self.base / "claude-skills"
        self.project = self.base / "proj"
        self.project.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def shims(self) -> list[list[str]]:
        """この OS で `tri` として呼ばれる起動スクリプト（Windows では cmd と Git Bash の両方）。"""
        sh = self.bin / "tri"
        if os.name == "nt":
            out = [[str(self.bin / "tri.cmd")]]
            bash = shutil.which("bash")
            return out + ([[bash, sh.as_posix()]] if bash else [])
        return [[str(sh)]]

    def tri(self, shim: list[str], *args: str) -> str:
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONUTF8")}
        r = subprocess.run([*shim, *args], cwd=self.project, capture_output=True, env=env, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        return r.stdout.decode("utf-8")

    def test_shim_runs_cli_from_installed_copy(self):
        install.install(self.prefix, self.bin, [self.agents])
        for shim in self.shims():
            with self.subTest(shim=shim[-1]):
                shutil.rmtree(self.project)
                self.project.mkdir()
                self.tri(shim, "init", "--name", "x")
                self.assertIn("Tri-SSD 状況", self.tri(shim, "status"))
                self.assertIn("# context:", self.tri(shim, "context", "docs/goal.md", "--emit"))
                self.assertIn("# 知識モデル", self.tri(shim, "guide", "knowledge-model"))
        self.assertTrue((self.prefix / "templates" / "task.md").exists())

    def test_skills_are_agent_skills_copies(self):
        install.install(self.prefix, self.bin, [self.agents, self.claude])
        for skills in (self.agents, self.claude):
            self.assertEqual(sorted(p.name for p in skills.iterdir()), SKILL_NAMES)
            for name in SKILL_NAMES:
                text = (skills / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertEqual(re.search(r"^name: (.+)$", text, re.M).group(1), name)
                self.assertEqual(tree(skills / name), tree(ROOT / "skills" / name))

    def test_reinstall_converges_and_removes_what_is_gone(self):
        install.install(self.prefix, self.bin, [self.agents, self.claude])
        (self.prefix / "scripts" / "trissd" / "stale.py").write_text("", encoding="utf-8")
        (self.agents / SKILL_NAMES[0] / "stale.md").write_text("", encoding="utf-8")
        install.install(self.prefix, self.bin, [self.agents])
        self.assertFalse(self.claude.exists() and any(self.claude.iterdir()))
        self.assertFalse((self.prefix / "scripts" / "trissd" / "stale.py").exists())
        self.assertFalse((self.agents / SKILL_NAMES[0] / "stale.md").exists())
        before = tree(self.base)
        install.install(self.prefix, self.bin, [self.agents])
        self.assertEqual(tree(self.base), before)


if __name__ == "__main__":
    unittest.main()
