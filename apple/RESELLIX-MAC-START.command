#!/bin/bash
# Wrapper — runs the main starter at repo root.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec /bin/bash "$ROOT/RESELLIX-MAC-START.command"
