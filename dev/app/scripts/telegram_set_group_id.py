#!/usr/bin/env python3
"""Set TELEGRAM_CHAT_ID in dev/.env (usage: python scripts/telegram_set_group_id.py -1001234567890)."""
from __future__ import annotations

import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from config import ENV_PATH, load_config
from dotenv import set_key


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/telegram_set_group_id.py -1001234567890")
        print("Tip: /start in the group — bot replies with the id if not configured yet.")
        return 1
    group_id = sys.argv[1].strip()
    try:
        int(group_id)
    except ValueError:
        print("Chat id must be a number (group ids are negative, e.g. -100...)")
        return 1

    cfg = load_config()
    personal = cfg.telegram_chat_id_list()
    keep = input(f"Keep private chat {personal[0]} too? [y/N]: ").strip().lower() if personal else "n"
    if keep in ("y", "yes") and personal and int(group_id) != personal[0]:
        value = f"{group_id},{personal[0]}"
    else:
        value = group_id

    set_key(str(ENV_PATH), "TELEGRAM_CHAT_ID", value, quote_mode="never")
    print(f"Saved TELEGRAM_CHAT_ID={value}")
    print("Restart Resellix, then /start in the group.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
