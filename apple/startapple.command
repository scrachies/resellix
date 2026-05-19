#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV="$ROOT/dev"
APP="$DEV/app"
cd "$APP"

command -v python3 >/dev/null || { echo "Install Python 3.11+"; read -r; exit 1; }

VENV="$APP/.venv"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
PY="$VENV/bin/python"

"$PY" -m pip install -q --upgrade pip
"$PY" -m pip install -q -r "$APP/requirements.txt"
"$PY" -m pip install -q "pyvinted>=0.5.3" 2>/dev/null || true
[ -f "$APP/requirements-kleinanzeigen.txt" ] && \
  "$PY" -m pip install -q -r "$APP/requirements-kleinanzeigen.txt" 2>/dev/null || true

[ -f "$DEV/.env" ] || { [ -f "$ROOT/.env" ] && mv "$ROOT/.env" "$DEV/.env"; }
[ -f "$DEV/.env" ] || { [ -f "$DEV/.env.example" ] && cp "$DEV/.env.example" "$DEV/.env"; }

echo "[Update] Checking GitHub..."
"$PY" "$APP/github_update.py" || true
echo

export PYTHONUNBUFFERED=1
exec "$PY" "$APP/launch_resellix.py"
