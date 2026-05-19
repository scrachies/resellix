"""Sort options for ad-hoc Telegram / manual search."""
from __future__ import annotations

from typing import Optional

SORT_NEWEST = "newest"
SORT_OLDEST = "oldest"
SORT_CHEAPEST = "cheapest"
SORT_EXPENSIVE = "expensive"

SORT_LABELS = {
    SORT_NEWEST: "Newest first",
    SORT_OLDEST: "Oldest first",
    SORT_CHEAPEST: "Cheapest first",
    SORT_EXPENSIVE: "Most expensive first",
}


def parse_sort_reply(text: str) -> Optional[str]:
    t = (text or "").strip().lower()
    if not t:
        return None
    if t in ("1", "newest", "new", "neueste", "neu"):
        return SORT_NEWEST
    if t in ("2", "oldest", "old", "älteste", "alt"):
        return SORT_OLDEST
    if t in ("3", "cheapest", "cheap", "low", "günstig", "billig", "preis auf"):
        return SORT_CHEAPEST
    if t in ("4", "expensive", "high", "teuer", "highest", "preis ab"):
        return SORT_EXPENSIVE
    return None


def vinted_order_for_sort(sort: str) -> str:
    if sort == SORT_OLDEST:
        return "oldest_first"
    if sort == SORT_CHEAPEST:
        return "price_low_to_high"
    if sort == SORT_EXPENSIVE:
        return "price_high_to_low"
    return "newest_first"


def ebay_sop_for_sort(sort: str) -> str:
    # eBay.de _sop: 10=newly listed, 16=price+shipping highest, 15=lowest
    if sort == SORT_CHEAPEST:
        return "15"
    if sort == SORT_EXPENSIVE:
        return "16"
    return "10"
