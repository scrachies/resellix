#!/bin/bash
# No window — sniper + Telegram only (easier on Mac than the GUI)
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/dev/app"
DEV="$ROOT/dev"
LOG="/tmp/resellix-headless.log"

{
  echo "Resellix HEADLESS $(date)"
  xattr -cr "$ROOT" 2>/dev/null || true
  cd "$APP" || exit 1
  [ -x .venv/bin/python ] || python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
  [ -f "$DEV/.env" ] || cp "$DEV/.env.example" "$DEV/.env" 2>/dev/null || true
  export RESELLIX_SKIP_KA=1
  echo "Running — use Telegram /add /list /status. Ctrl+C to stop."
  exec .venv/bin/python -u main.py --headless
} 2>&1 | tee -a "$LOG"

echo "Log: $LOG"
read -r
