#!/usr/bin/env bash
# Tri-SSD を導入していない小さな CLI プロジェクトを作業ディレクトリに複製する
set -euo pipefail
cp -R "$(dirname "$0")/../neg-docs-other-repo/project/." .
git init -q && git add -A && git -c user.email=eval@example.com -c user.name=eval commit -qm init
