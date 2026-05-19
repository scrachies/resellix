#!/bin/bash
# Paste entire apple/friend-run.sh in Terminal, or:  bash apple/friend-run.sh

echo ""
echo "========== RESELLIX START =========="
echo ""

ROOT=""
for d in "$HOME/Desktop/resellix" "$HOME/Downloads/resellix" "$HOME/Documents/resellix" "$HOME/resellix"; do
  if [ -f "$d/dev/app/main.py" ]; then
    ROOT="$d"
    break
  fi
done

if [ -z "$ROOT" ]; then
  echo "ERROR: resellix folder not found."
  echo "Expected: ~/Desktop/resellix/dev/app/main.py"
  echo ""
  echo "Clone first:"
  echo "  git clone https://github.com/scrachies/resellix.git ~/Desktop/resellix"
  echo ""
  echo "Press Enter to close..."
  read -r
  exit 1
fi

cd "$ROOT" || exit 1
echo "Using folder: $(pwd)"
echo ""

if [ -d .git ]; then
  echo "Git pull..."
  git pull --ff-only origin main || echo "WARNING: git pull failed (ask Thomas for GitHub access)"
  echo ""
else
  echo "No .git folder — skipping git pull"
  echo ""
fi

xattr -cr . 2>/dev/null || true
chmod +x apple/*.command 2>/dev/null || true

echo "Launching Resellix..."
echo ""
exec bash apple/startapple.command
