"""標準入出力と子プロセス出力の文字コード: ロケールが UTF-8 でない環境（Windows の cp932 など）でも UTF-8 で扱う。

CLI を別プロセスで起動し、Python の入出力の既定を UTF-8 以外にして確かめる。
子プロセスの出力の読み方はロケールに従うので、その検査はロケールが UTF-8 でない環境（Windows）でだけ不具合を検出する。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

TRI = ROOT / "scripts" / "tri.py"
TEXT = "- 現在位置: T-0005 の AC1 PASS\n- 次の一手: 補完の並び順（日本語）\n"


def non_utf8_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env["PYTHONIOENCODING"] = "ascii:strict"  # 標準入出力だけを UTF-8 以外にする（ファイル名の文字コードは変えない）
    return env


def run(*args: str, root: Path, stdin: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TRI), "--root", str(root), *args], input=stdin,
                          capture_output=True, env=non_utf8_env(), timeout=120)


class IoEncodingTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "日本語のプロジェクト"
        self.root.mkdir()
        self.assertEqual(run("init", "--name", "x", root=self.root).returncode, 0)

    def tearDown(self):
        self._tmp.cleanup()

    def test_handoff_reads_japanese_stdin_as_utf8(self):
        r = run("handoff", "-", root=self.root, stdin=TEXT.encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertIn(TEXT.strip(), (self.root / "docs/notes/handoff.md").read_text(encoding="utf-8"))
        self.assertIn("更新:", r.stdout.decode("utf-8"))

    def test_hook_reads_japanese_cwd_from_stdin_json(self):
        payload = json.dumps({"cwd": str(self.root)}, ensure_ascii=False).encode("utf-8")
        r = run("status", "--hook", root=Path(self._tmp.name), stdin=payload)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertIn("Tri-SSD", r.stdout.decode("utf-8"))

    def test_verify_records_utf8_output_of_command(self):
        self.assertEqual(run("task", "new", "Encoding", root=self.root).returncode, 0)
        task = next((self.root / "docs/tasks").glob("T-*.md"))
        py = f'"{sys.executable}"' if " " in sys.executable else sys.executable
        cmd = py + " -c \"import sys; sys.stdout.buffer.write('\\u65e5\\u672c\\u8a9e'.encode('utf-8'))\""
        text = task.read_text(encoding="utf-8")
        start = text.index("- AC1:")
        end = text.index("## メモ")
        task.write_text(text[:start] + f"- AC1: 日本語を出力する\n  - 検証: `{cmd}`\n\n" + text[end:], encoding="utf-8")
        r = run("task", "verify", "-".join(task.stem.split("-")[:2]), root=self.root)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertIn("AC1 PASS", task.read_text(encoding="utf-8"))
        self.assertIn("「日本語」", task.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
