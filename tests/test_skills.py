"""配布物としての契約: Skill の書式（Agent Skills）・参照の実在・フックの登録例・版番号・README。"""
import argparse
import json
import re
import unittest

from helpers import ROOT, tri
from trissd import md

SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))


def subcommands(parser: argparse.ArgumentParser) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            for name, sub in act.choices.items():
                out[name] = set()
                for a2 in sub._actions:
                    if isinstance(a2, argparse._SubParsersAction):
                        out[name] = set(a2.choices)
    return out


class SkillTest(unittest.TestCase):
    def test_skill_set(self):
        self.assertEqual([p.parent.name for p in SKILLS], ["tri-ssd-docs", "tri-ssd-setup", "tri-ssd-task"])

    def test_frontmatter_and_size(self):
        for path in SKILLS:
            text = path.read_text(encoding="utf-8")
            fm, start = md.parse_frontmatter(text)
            with self.subTest(skill=path.parent.name):
                self.assertEqual(fm.get("name"), path.parent.name)
                self.assertTrue(fm.get("description"))
                self.assertLessEqual(len(fm["description"]), 1024)
                self.assertNotIn("when_to_use", fm)
                self.assertLess(len(text.splitlines()) - start, 500)
                self.assertIn("## 完了後の案内", text)

    def test_shared_context_block_is_identical(self):
        blocks = {re.search(r"<tri_ssd_context>.*?</tri_ssd_context>", p.read_text(encoding="utf-8"), re.S).group(0)
                  for p in SKILLS}
        self.assertEqual(len(blocks), 1)
        self.assertIn("avoid_over_engineering", SKILLS[0].read_text(encoding="utf-8"))

    def test_references_resolve_without_agent_specific_paths(self):
        for path in SKILLS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=path.parent.name):
                self.assertNotRegex(text, r"\$\{\w+\}|scripts/tri\.py")
                for ref in re.findall(r"`(references/[^`]+)`", text):
                    self.assertTrue((path.parent / ref).exists(), ref)
                for name in re.findall(r"`tri guide ([^`]+)`", text):
                    self.assertIn(name, tri.GUIDE_NAMES)

    def test_cli_commands_in_skills_exist(self):
        cmds = subcommands(tri.build_parser())
        for path in SKILLS:
            for line in path.read_text(encoding="utf-8").splitlines():
                for m in re.finditer(r"(?:^|[`\s(])tri ([a-z]+)(?: ([a-z]+))?", line):
                    cmd, sub = m.group(1), m.group(2)
                    with self.subTest(skill=path.parent.name, line=line.strip()):
                        self.assertIn(cmd, cmds)
                        if cmds[cmd]:
                            self.assertIn(sub, cmds[cmd])


class ReadmeTest(unittest.TestCase):
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_covers_usage(self):
        for heading in ("## インストール", "## 初期化", "## 日常の使い方", "## 既存プロジェクトへの導入", "## 旧 Tri-SSD からの移行"):
            self.assertIn(heading, self.text)
        self.assertIn("python scripts/install.py", self.text)
        self.assertNotRegex(self.text, r"/plugin (install|marketplace)")

    def test_hook_registration_example(self):
        block = next(b for b in re.findall(r"```json\n(.*?)```", self.text, re.S) if '"hooks"' in b)
        hooks = json.loads(block)["hooks"]
        self.assertEqual(set(hooks), {"SessionStart", "PostToolUse"})
        cmds = subcommands(tri.build_parser())
        for groups in hooks.values():
            for g in groups:
                for h in g["hooks"]:
                    self.assertEqual(h["type"], "command")
                    m = re.match(r"tri (\w+) --hook\b", h["command"])
                    self.assertIsNotNone(m, h["command"])
                    self.assertIn(m.group(1), cmds)


class ReleaseTest(unittest.TestCase):
    def test_versions_in_sync(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        changelog = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(plugin, changelog)


if __name__ == "__main__":
    unittest.main()
