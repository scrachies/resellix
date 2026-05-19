#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP="$DIR/dev/app"
cd "$DIR"

command -v git >/dev/null || { echo "Install git (xcode-select --install)"; read -r; exit 1; }
[ -d .git ] || { echo "Clone first: git clone https://github.com/scrachies/resellix.git"; read -r; exit 1; }

echo "[Update] github.com/scrachies/resellix ..."
git pull --ff-only

[ -x "$APP/.venv/bin/python" ] && "$APP/.venv/bin/python" -m pip install -q -r "$APP/requirements.txt"
[ -f "$APP/requirements-kleinanzeigen.txt" ] && [ -x "$APP/.venv/bin/python" ] && \
  "$APP/.venv/bin/python" -m pip install -q -r "$APP/requirements-kleinanzeigen.txt" 2>/dev/null || true

echo "[OK] Run apple/startapple.command"
read -r
