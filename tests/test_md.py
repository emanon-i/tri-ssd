import unittest

import helpers  # noqa: F401
from trissd import md


class FrontmatterTest(unittest.TestCase):
    def test_inline_block_and_quotes(self):
        text = "---\nid: T-0001\nrefs: [REQ-0001, 'docs/a.md#x']\ncode:\n  - src/a/\n  - \"src/b.py\"\n---\n# T\n"
        fm, start = md.parse_frontmatter(text)
        self.assertEqual(fm["id"], "T-0001")
        self.assertEqual(fm["refs"], ["REQ-0001", "docs/a.md#x"])
        self.assertEqual(fm["code"], ["src/a/", "src/b.py"])
        self.assertEqual(start, 7)

    def test_set_value_keeps_other_lines(self):
        text = "---\nid: T-0001\nstatus: open\n---\nbody\n"
        out = md.set_fm_value(text, "status", "done")
        self.assertIn("status: done", out)
        self.assertIn("id: T-0001", out)
        out = md.set_fm_value(out, "closed", "2026-10-16")
        self.assertEqual(md.parse_frontmatter(out)[0]["closed"], "2026-10-16")
        self.assertTrue(out.endswith("body\n"))


class SectionTest(unittest.TestCase):
    def test_sections_slugs_and_fences(self):
        text = "# A\nintro\n## B b\n```\n# not heading\n```\n### C\nx\n## B b\n"
        secs = md.split_sections("d.md", text)
        self.assertEqual([s.title for s in secs[1:]], ["A", "B b", "C", "B b"])
        self.assertEqual([s.slug for s in secs[1:]], ["a", "b-b", "c", "b-b-1"])
        self.assertEqual(secs[2].parent, 1)
        self.assertEqual(secs[3].parent, 2)
        self.assertIn("# not heading", secs[2].text)
        self.assertEqual(secs[2].subtree_end, 8)

    def test_japanese_slug(self):
        self.assertEqual(md.slugify("REQ-0004 タグ検索"), "req-0004-タグ検索")
        self.assertEqual(md.slugify("GET /tags/suggest"), "get-tagssuggest")
        self.assertEqual(md.slugify("エラー処理（方針）"), "エラー処理方針")


class RefTest(unittest.TestCase):
    def test_ids_exclude_inline_code(self):
        self.assertEqual(md.ids_in("see REQ-0001 and `T-0002`, not XREQ-0003 or REQ-00041"), ["REQ-0001"])

    def test_links(self):
        line = "[a](b.md#x) [u](https://x.org) `[c](d.md)` ![img](p.png)"
        self.assertEqual(md.links_in(line), ["b.md#x"])

    def test_code_spans(self):
        self.assertEqual(md.code_spans("`src/a.py:12` `npm test` `x` `src/*.py` `./b/c/`"), ["src/a.py", "src/*.py", "b/c/"])

    def test_prose_lines_skip_fence_and_comments(self):
        text = "a REQ-0001\n```\nREQ-0002\n```\n<!-- REQ-0003 -->\n"
        ids = [i for _, line in md.prose_lines(text) for i in md.ids_in(line)]
        self.assertEqual(ids, ["REQ-0001"])

    def test_token_estimate(self):
        self.assertEqual(md.estimate_tokens("abcd" * 100), 101)
        self.assertEqual(md.estimate_tokens("日本語" * 10), 31)


if __name__ == "__main__":
    unittest.main()
