#!/usr/bin/env bash
# tests/fixtures/v5project（旧 Tri-SSD の L0〜L3 構成）を作業ディレクトリに複製する
set -euo pipefail
cp -R "$(dirname "$0")/../../tests/fixtures/v5project/." .
git init -q && git add -A && git -c user.email=eval@example.com -c user.name=eval commit -qm init
