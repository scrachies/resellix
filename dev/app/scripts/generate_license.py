#!/usr/bin/env python3
"""Generate signed Resellix license keys (run from dev/app)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

from subscription import generate_license_key


def main() -> int:
    p = argparse.ArgumentParser(description="Generate Resellix license keys")
    p.add_argument(
        "tier",
        choices=["plus", "pro", "max", "updates"],
        help="plus | pro | max (subscription) | updates (extends git updates)",
    )
    p.add_argument("--updates-days", type=int, default=30, help="Days of git updates")
    p.add_argument("--subscription-days", type=int, default=30, help="Max subscription days")
    args = p.parse_args()

    key = generate_license_key(
        args.tier,
        updates_days=args.updates_days,
        subscription_days=args.subscription_days,
    )
    print(key)
    print()
    labels = {
        "plus": "Resellix Plus — 2 snipes, Vinted only, slower alerts.",
        "pro": "Resellix Pro — 5 snipes, all platforms, cheap deals, chat search.",
        "max": f"Resellix Max — full access + beta ({args.subscription_days} days).",
        "updates": "Updates extension — extends git updates period.",
    }
    print(labels.get(args.tier, ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
