#!/usr/bin/env python3
"""Find Telegram group chat ID and write it to dev/.env (TELEGRAM_CHAT_ID)."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from config import ENV_PATH, load_config
from dotenv import set_key


def main() -> int:
    cfg = load_config()
    token = (cfg.telegram_bot_token or "").strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN missing in dev/.env")
        return 1

    print("1) Create a Telegram group, add your Resellix bot + your friend.")
    print("2) In the group send:  /start")
    print("3) In @BotFather send:  /setprivacy  ->  Disable  (so the bot sees commands in groups)")
    print()
    input("Press Enter when done...")
    print()

    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=30"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if not data.get("ok"):
        print("Telegram API error:", data)
        return 1

    chats: dict[int, str] = {}
    for item in data.get("result", []):
        msg = item.get("message") or item.get("channel_post") or {}
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        if cid is None:
            continue
        title = chat.get("title") or chat.get("first_name") or chat.get("username") or "?"
        kind = chat.get("type", "?")
        chats[int(cid)] = f"{title} ({kind})"

    if not chats:
        print("No messages found. Send /start in the group, then run this script again.")
        return 1

    print("Chats seen recently:")
    for i, (cid, label) in enumerate(chats.items(), 1):
        print(f"  {i}. {cid}  —  {label}")

    groups = {cid: label for cid, label in chats.items() if "group" in label or "supergroup" in label}
    pick: int | None = None
    if len(groups) == 1:
        pick = next(iter(groups))
        print(f"\nUsing group: {pick} ({groups[pick]})")
    else:
        raw = input("\nPaste the GROUP chat id (negative number, e.g. -100...): ").strip()
        try:
            pick = int(raw)
        except ValueError:
            print("Invalid id")
            return 1

    personal = cfg.telegram_chat_id_list()
    keep_personal = input(
        f"Also keep your private chat ({personal[0] if personal else 'none'}) for alerts? [y/N]: "
    ).strip().lower()
    if keep_personal in ("y", "yes") and personal:
        new_val = f"{pick},{personal[0]}"
    else:
        new_val = str(pick)

    set_key(str(ENV_PATH), "TELEGRAM_CHAT_ID", new_val, quote_mode="never")
    print(f"\nSaved TELEGRAM_CHAT_ID={new_val} in dev/.env")
    print("Restart Resellix, then /start in the group.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
