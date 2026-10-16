"""プラグインとしての契約: Skill の書式・CLI 参照の実在・フック・版番号・README。"""
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
        self.assertEqual([p.parent.name for p in SKILLS], ["docs", "note", "setup", "task"])

    def test_frontmatter_and_size(self):
        for path in SKILLS:
            text = path.read_text(encoding="utf-8")
            fm, start = md.parse_frontmatter(text)
            with self.subTest(skill=path.parent.name):
                self.assertTrue(fm.get("description"))
                self.assertTrue(fm.get("when_to_use"))
                self.assertLessEqual(len(fm["description"]) + len(fm["when_to_use"]), 1536)
                self.assertNotIn("name", fm)
                self.assertLess(len(text.splitlines()) - start, 500)
                self.assertIn("## 完了後の案内", text)

    def test_shared_context_block_is_identical(self):
        blocks = {re.search(r"<tri_ssd_context>.*?</tri_ssd_context>", p.read_text(encoding="utf-8"), re.S).group(0)
                  for p in SKILLS}
        self.assertEqual(len(blocks), 1)
        self.assertIn("avoid_over_engineering", SKILLS[0].read_text(encoding="utf-8"))

    def test_referenced_files_exist(self):
        for path in SKILLS:
            for ref in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([^\s`\"]+)", path.read_text(encoding="utf-8")):
                with self.subTest(skill=path.parent.name, ref=ref):
                    self.assertTrue((path.parent / ref).resolve().exists())

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


class HookTest(unittest.TestCase):
    def test_hooks_schema(self):
        data = json.loads((ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data["hooks"]), {"SessionStart", "PostToolUse"})
        for event, groups in data["hooks"].items():
            for g in groups:
                for h in g["hooks"]:
                    self.assertEqual(h["type"], "command")
                    m = re.search(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+?)\"? (\w+) --hook", h["command"])
                    self.assertIsNotNone(m, h["command"])
                    self.assertTrue((ROOT / m.group(1)).exists())
                    self.assertIn(m.group(2), subcommands(tri.build_parser()))


class ReleaseTest(unittest.TestCase):
    def test_versions_in_sync(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))["plugins"][0]["version"]
        changelog = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(plugin, market)
        self.assertEqual(plugin, changelog)

    def test_readme_covers_usage(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for heading in ("## インストール", "## 初期化", "## 日常の使い方", "## 既存プロジェクトへの導入", "## 旧 Tri-SSD からの移行"):
            self.assertIn(heading, text)


if __name__ == "__main__":
    unittest.main()
