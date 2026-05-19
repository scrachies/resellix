#!/bin/bash
# Resellix Mac — double-click this file OR run:  bash apple/startapple.command

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV="$ROOT/dev"
APP="$DEV/app"

echo "=============================================="
echo "  Resellix"
echo "  Folder: $ROOT"
echo "=============================================="
echo

if command -v xattr >/dev/null 2>&1; then
  xattr -dr com.apple.quarantine "$ROOT" 2>/dev/null || true
fi
chmod -R u+rwX "$ROOT" 2>/dev/null || true
chmod +x "$ROOT/apple/"*.command 2>/dev/null || true

if [ ! -f "$APP/main.py" ]; then
  echo "[ERROR] Incomplete folder — missing dev/app/main.py"
  echo "        Unzip the full resellix zip or run:  ls \"$ROOT/dev/app\""
  echo
  echo "Press Enter to close..."
  read -r
  exit 1
fi

cd "$APP" || {
  echo "[ERROR] Cannot open: $APP"
  echo "Press Enter to close..."
  read -r
  exit 1
}

if ! command -v python3 >/dev/null; then
  echo "[ERROR] Python 3.11+ required: https://www.python.org/downloads/"
  echo "Press Enter to close..."
  read -r
  exit 1
fi

echo "[1/4] Python: $(python3 --version 2>&1)"
echo

VENV="$APP/.venv"
if [ ! -x "$VENV/bin/python" ]; then
  echo "[2/4] Creating virtual environment (first run only)..."
  python3 -m venv "$VENV" || {
    echo "[ERROR] Could not create .venv — move folder to Desktop/Documents."
    echo "Press Enter to close..."
    read -r
    exit 1
  }
else
  echo "[2/4] Virtual environment OK"
fi
PY="$VENV/bin/python"
echo

echo "[3/4] Installing packages — can take 5–15 min, window is NOT frozen:"
echo
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r "$APP/requirements.txt"
if [ -f "$APP/requirements-kleinanzeigen.txt" ]; then
  "$PY" -m pip install -r "$APP/requirements-kleinanzeigen.txt" 2>/dev/null || true
fi
echo
echo "[3/4] Packages done."
echo

if [ ! -f "$DEV/.env" ]; then
  [ -f "$ROOT/.env" ] && mv "$ROOT/.env" "$DEV/.env"
  [ -f "$DEV/.env" ] || { [ -f "$DEV/.env.example" ] && cp "$DEV/.env.example" "$DEV/.env"; }
fi

echo "[4/4] Checking GitHub updates (optional)..."
"$PY" "$APP/github_update.py" || echo "[Update] skipped — app will still start."
echo
echo "Starting Resellix window..."
echo "(Leave this Terminal open while the app runs.)"
echo

export PYTHONUNBUFFERED=1
"$PY" "$APP/launch_resellix.py"
EXIT=$?

if [ "$EXIT" != "0" ]; then
  echo
  echo "[ERROR] Resellix exited with code $EXIT"
fi
echo
echo "Press Enter to close this window..."
read -r
exit "$EXIT"
