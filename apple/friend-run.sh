#!/bin/bash
# Full paste script — or after git pull:  bash apple/friend-run.sh
LOG="/tmp/resellix-start.log"
echo "Resellix friend-run $(date)" >> "$LOG"

ROOT=""
for d in "$HOME/Desktop/resellix" "$HOME/Downloads/resellix" "$HOME/Documents/resellix" "$HOME/resellix"; do
  if [ -f "$d/dev/app/main.py" ]; then ROOT="$d"; break; fi
done

if [ -z "$ROOT" ]; then
  echo "ERROR: no resellix folder. Run:"
  echo "git clone https://github.com/scrachies/resellix.git ~/Desktop/resellix"
  read -r
  exit 1
fi

cd "$ROOT" || exit 1
echo "Folder: $(pwd)"

[ -d .git ] && git pull --ff-only origin main 2>&1 | tee -a "$LOG" || true
xattr -cr . 2>/dev/null || true
chmod +x apple/*.command 2>/dev/null || true

exec /bin/bash apple/startapple.command
