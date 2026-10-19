#!/usr/bin/env python3
"""Tri-SSD を導入する。CLI の実行一式・起動スクリプト `tri`・Skill の写しを置く（リンクは作らない）。

    python scripts/install.py [--prefix DIR] [--bin DIR] [--skills DIR ...]

置いたファイルの一覧を <prefix>/install.json に記録し、次の導入で一覧から消えたものを削除する。
何度実行しても同じ状態になる。標準ライブラリのみ。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ("scripts/tri.py", "scripts/trissd", "templates", "docs/knowledge-model.md", "docs/writing-rules.md")
MANIFEST = "install.json"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def skill_sources() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "skills").glob("*/SKILL.md"))


def _remove(path: Path) -> None:
    if path.is_symlink() or getattr(os.path, "isjunction", lambda _: False)(path):
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _copy(src: Path, dst: Path) -> None:
    _remove(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, ignore=IGNORE)
    else:
        shutil.copy2(src, dst)


def _write_shims(bin_dir: Path, prefix: Path, python: str) -> list[Path]:
    bin_dir.mkdir(parents=True, exist_ok=True)
    entry = prefix / "scripts" / "tri.py"
    sh = bin_dir / "tri"
    sh.write_bytes(f'#!/bin/sh\nexec "{Path(python).as_posix()}" "{entry.as_posix()}" "$@"\n'.encode("utf-8"))
    sh.chmod(0o755)
    shims = [sh]
    if os.name == "nt":
        cmd = bin_dir / "tri.cmd"
        cmd.write_bytes(f'@echo off\r\n"{python}" "{entry}" %*\r\nexit /b %ERRORLEVEL%\r\n'.encode("oem"))
        shims.append(cmd)
    return shims


def install(prefix: Path, bin_dir: Path, skill_dirs: list[Path], python: str = sys.executable) -> list[Path]:
    """導入して、置いた起動スクリプトと Skill のパスを返す。"""
    prefix, bin_dir = prefix.resolve(), bin_dir.resolve()
    manifest = prefix / MANIFEST
    previous = set(json.loads(manifest.read_text(encoding="utf-8"))["paths"]) if manifest.exists() else set()
    for rel in RUNTIME:
        _copy(ROOT / rel, prefix / rel)
    placed = _write_shims(bin_dir, prefix, python)
    for skills in skill_dirs:
        for src in skill_sources():
            _copy(src, skills.resolve() / src.name)
            placed.append(skills.resolve() / src.name)
    for stale in previous - {str(p) for p in placed}:
        _remove(Path(stale))
    manifest.write_text(json.dumps({"paths": sorted(str(p) for p in placed)}, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    return placed


def on_path(bin_dir: Path) -> bool:
    want = os.path.normcase(str(bin_dir.resolve()))
    return any(os.path.normcase(os.path.abspath(d)) == want for d in os.environ.get("PATH", "").split(os.pathsep) if d)


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    home = Path.home()
    ap = argparse.ArgumentParser(prog="install.py", description="Tri-SSD の CLI と Skill を導入する")
    ap.add_argument("--prefix", type=Path, default=home / ".local/share/tri-ssd", help="CLI の実行一式を置く場所")
    ap.add_argument("--bin", type=Path, default=home / ".local/bin", help="起動スクリプト tri を置く場所（PATH の通ったフォルダ）")
    ap.add_argument("--skills", type=Path, action="append", help="Skill を写す場所（複数可。既定 ~/.agents/skills）")
    a = ap.parse_args(argv)
    placed = install(a.prefix, a.bin, a.skills or [home / ".agents/skills"])
    print("# Tri-SSD 導入\n")
    print(f"- CLI: {a.prefix.resolve()}")
    print("\n".join(f"- {p}" for p in placed))
    if not on_path(a.bin):
        print(f"\n⚠️  {a.bin.resolve()} が PATH にありません。PATH に足すと `tri` で呼べます")
    print("\n次: Claude Code ではフックを ~/.claude/settings.json に登録する（README の「インストール」）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
