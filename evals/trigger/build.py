"""queries.json（発火評価の依頼と、固定した学習・検証の分割）から claude plugin eval のケースを生成する。

    python3 evals/trigger/build.py            # evals/trigger/cases/ に生成（git 管理外）
    claude plugin eval . --tag trigger --tag train --ablation none --scaffold --allow-tools Bash Write Edit

依頼ごとに、期待するスキルが呼ばれたか・他のスキルが呼ばれなかったかを Skill の呼び出しで判定する。
分割は作成時に一度だけ決めて queries.json に書いてある。説明文を直すときは train の失敗だけを見る。
"""
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ("task", "docs", "setup")
# 作業ディレクトリに複製する題材（ケースのディレクトリからの相対パス）
WORKSPACES = {
    "linkbox": "../../../../tests/fixtures/linkbox",
    "v5project": "../../../../tests/fixtures/v5project",
    "wcount": "../../../neg-docs-other-repo/project",
}


def case_yaml(q: dict) -> str:
    graders = []
    for s in SKILLS:
        expected = q["expect"] == s
        graders.append(
            f"  - name: {'fires' if expected else 'not'}-{s}\n"
            "    type: tool_used\n"
            "    tool: Skill\n"
            f"    input_match: '\"skill\"\\s*:\\s*\"(?:tri-ssd:)?{s}\"'\n"
            + ("" if expected else "    min: 0\n    max: 0\n"))
    prompt = "\n".join("    " + line for line in q["query"].splitlines())
    return (
        'schema_version: "1.1"\n'
        f"name: trigger-{q['id']}\n"
        f"tags: [trigger, {q['split']}, expect-{q['expect']}]\n"
        'plugins: ["../../../.."]\n'
        "context:\n  scaffold_script: fixture.sh\n"
        "execution:\n  max_turns: 6\n  timeout_seconds: 240\n"
        "  allowed_tools: [Read, Glob, Grep, Skill]\n"
        f"  prompt: |\n{prompt}\n"
        "graders:\n" + "".join(graders))


def fixture_sh(q: dict) -> str:
    return (
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        f'cp -R "$(dirname "$0")/{WORKSPACES[q["workspace"]]}/." .\n'
        "git init -q && git add -A && git -c user.email=eval@example.com -c user.name=eval commit -qm init\n")


def main():
    out = HERE / "cases"
    shutil.rmtree(out, ignore_errors=True)
    for q in json.loads((HERE / "queries.json").read_text(encoding="utf-8")):
        d = out / q["id"]
        d.mkdir(parents=True)
        (d / "case.yaml").write_text(case_yaml(q), encoding="utf-8")
        (d / "fixture.sh").write_text(fixture_sh(q), encoding="utf-8")
        (d / "fixture.sh").chmod(0o755)
    print(f"生成: {out}")


if __name__ == "__main__":
    main()
