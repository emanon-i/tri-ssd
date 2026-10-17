#!/usr/bin/env bash
# tests/fixtures/linkbox（Tri-SSD 導入済みの架空プロジェクト）を作業ディレクトリに複製する
set -euo pipefail
cp -R "$(dirname "$0")/../../tests/fixtures/linkbox/." .
git init -q && git add -A && git -c user.email=eval@example.com -c user.name=eval commit -qm init
