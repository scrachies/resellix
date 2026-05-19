#!/bin/bash
# Double-click or: bash apple/startapple.command
LOG="/tmp/resellix-start.log"
{
  echo "======== $(date) ========"
  echo "Resellix Mac start"

  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
  DEV="$ROOT/dev"
  APP="$DEV/app"
  echo "ROOT=$ROOT"

  if command -v xattr >/dev/null 2>&1; then
    xattr -dr com.apple.quarantine "$ROOT" 2>/dev/null || true
  fi
  chmod -R u+rwX "$ROOT" 2>/dev/null || true
  chmod +x "$ROOT/apple/"*.command 2>/dev/null || true

  if [ ! -f "$APP/main.py" ]; then
    echo "ERROR: missing $APP/main.py — unzip or git clone the full resellix folder"
    exit 1
  fi

  cd "$APP" || exit 1

  if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
  fi
  echo "Python: $(python3 --version 2>&1)"

  VENV="$APP/.venv"
  if [ ! -x "$VENV/bin/python" ]; then
    echo "Creating .venv..."
    python3 -m venv "$VENV" || exit 1
  fi
  PY="$VENV/bin/python"

  echo "Installing packages (first run: 5-15 min)..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r "$APP/requirements.txt" || exit 1

  if [ ! -f "$DEV/.env" ]; then
    [ -f "$DEV/.env.example" ] && cp "$DEV/.env.example" "$DEV/.env"
  fi

  echo "Testing PyQt6..."
  if ! "$PY" -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')" 2>&1; then
    echo "Installing PyQt6..."
    "$PY" -m pip install "PyQt6>=6.6.0" || exit 1
  fi

  export PYTHONUNBUFFERED=1
  export RESELLIX_SKIP_KA=1
  export QT_MAC_WANTS_LAYER=1

  echo "Starting app (Kleinanzeigen skipped on first Mac start)..."
  "$PY" -u "$APP/main.py"
  CODE=$?
  echo "main.py exit code: $CODE"

  if [ -f "$DEV/startup_error.log" ]; then
    echo "--- startup_error.log ---"
    cat "$DEV/startup_error.log"
  fi
  exit "$CODE"
} 2>&1 | tee -a "$LOG"

echo ""
echo "Log saved: $LOG"
echo "Press Enter to close..."
read -r </dev/tty 2>/dev/null || read -r
