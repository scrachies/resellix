#!/bin/bash
# =============================================================================
#  RESELLIX — Mac one-file starter (send this file to your friend)
#
#  1. Put this file INSIDE the unzipped "resellix" folder (next to apple/ dev/)
#  2. Double-click it  OR  Terminal:  bash RESELLIX-MAC-START.command
# =============================================================================

pause_at_end() {
  echo
  echo "=============================================="
  echo "  Press ENTER to close this window..."
  echo "=============================================="
  read -r </dev/tty 2>/dev/null || read -r
}

fail() {
  echo
  echo "[FEHLER] $*"
  echo
  pause_at_end
  exit 1
}

log() {
  echo
  echo ">>> $*"
}

# --- find project root ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT=""

if [ -f "$SCRIPT_DIR/dev/app/main.py" ]; then
  ROOT="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/resellix/dev/app/main.py" ]; then
  ROOT="$SCRIPT_DIR/resellix"
else
  for TRY in \
    "$HOME/Desktop/resellix" \
    "$HOME/Downloads/resellix" \
    "$HOME/Documents/resellix" \
    "$HOME/resellix"
  do
    if [ -f "$TRY/dev/app/main.py" ]; then
      ROOT="$TRY"
      break
    fi
  done
fi

echo "=============================================="
echo "  RESELLIX — Mac installer / starter"
echo "=============================================="

if [ -z "$ROOT" ]; then
  echo
  echo "Could not find Resellix folder (need dev/app/main.py)."
  echo
  echo "Put RESELLIX-MAC-START.command inside the resellix folder, e.g.:"
  echo "  Desktop/resellix/RESELLIX-MAC-START.command"
  echo
  echo "Or tell Thomas where you unzipped the zip."
  pause_at_end
  exit 1
fi

DEV="$ROOT/dev"
APP="$DEV/app"
LOG="$DEV/mac-start.log"
mkdir -p "$DEV"

log "Using folder: $ROOT"
log "Log file: $LOG"

{
  echo "======== $(date) ========"

  if command -v xattr >/dev/null 2>&1; then
    log "Removing macOS quarantine..."
    xattr -dr com.apple.quarantine "$ROOT" 2>/dev/null || true
  fi

  chmod -R u+rwX "$ROOT" 2>/dev/null || true
  [ -d "$ROOT/apple" ] && chmod +x "$ROOT/apple/"*.command 2>/dev/null || true
  chmod +x "$ROOT/RESELLIX-MAC-START.command" 2>/dev/null || true

  if [ ! -f "$APP/main.py" ]; then
    fail "Incomplete install — missing $APP/main.py"
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    fail "Python 3 is not installed. Install from https://www.python.org/downloads/ then run this again."
  fi

  log "Python: $(python3 --version 2>&1)"

  cd "$APP" || fail "Cannot cd to $APP"

  VENV="$APP/.venv"
  if [ ! -x "$VENV/bin/python" ]; then
    log "Creating virtual environment (first run)..."
    python3 -m venv "$VENV" || fail "Could not create .venv — move resellix to Desktop or Documents."
  fi

  PY="$VENV/bin/python"
  log "Using: $PY"

  log "Upgrading pip..."
  "$PY" -m pip install --upgrade pip || fail "pip upgrade failed"

  log "Installing requirements (5–15 minutes first time — please wait)..."
  "$PY" -m pip install -r "$APP/requirements.txt" || fail "pip install requirements.txt failed"

  if [ -f "$APP/requirements-kleinanzeigen.txt" ]; then
    log "Installing Kleinanzeigen extras (optional)..."
    "$PY" -m pip install -r "$APP/requirements-kleinanzeigen.txt" 2>/dev/null || true
  fi

  if [ ! -f "$DEV/.env" ]; then
    [ -f "$ROOT/.env" ] && mv "$ROOT/.env" "$DEV/.env"
    [ -f "$DEV/.env" ] || { [ -f "$DEV/.env.example" ] && cp "$DEV/.env.example" "$DEV/.env"; }
  fi

  log "Checking PyQt6..."
  if ! "$PY" -c "import PyQt6" 2>/dev/null; then
    log "Installing PyQt6..."
    "$PY" -m pip install PyQt6 || fail "PyQt6 install failed"
  fi

  log "GitHub update check (optional)..."
  "$PY" "$APP/github_update.py" 2>/dev/null || echo "(Update skipped — OK)"

  export PYTHONUNBUFFERED=1
  export QT_MAC_WANTS_LAYER=1

  log "Starting Resellix app window..."
  echo "(When you quit Resellix, you will return here.)"
  echo

  "$PY" "$APP/launch_resellix.py"
  CODE=$?

  echo
  if [ "$CODE" = "0" ]; then
    log "Resellix closed normally (exit 0)."
  else
    echo "[FEHLER] Resellix ended with exit code $CODE"
    if [ -f "$DEV/startup_error.log" ]; then
      echo
      echo "--- startup_error.log ---"
      cat "$DEV/startup_error.log"
      echo "--- end ---"
    fi
  fi

} 2>&1 | tee -a "$LOG"

pause_at_end
exit 0
