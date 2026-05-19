"""Format ad-hoc search hits for Telegram (title, price, description, location)."""
from __future__ import annotations

import html
import re

from platforms import platform_label
from vinted import Listing


def _clip(text: str, max_len: int) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def listing_detail_blurb(listing: Listing) -> str:
    """Short non-title facts when description is empty."""
    bits: list[str] = []
    if listing.brand:
        bits.append(listing.brand)
    if listing.size:
        bits.append(f"Size {listing.size}")
    if listing.status:
        bits.append(listing.status)
    return " · ".join(bits)


def format_search_result_block(
    index: int,
    platform: str,
    listing: Listing,
) -> str:
    plabel = platform_label(platform)
    title = html.escape(_clip(listing.title or "—", 140))
    price = f"{listing.price:.2f} {listing.currency or 'EUR'}"
    loc = _clip(listing.location or "", 80)
    desc = _clip(listing.description or "", 220)
    if not desc:
        desc = html.escape(_clip(listing_detail_blurb(listing), 220))
    else:
        desc = html.escape(desc)

    lines = [
        f"<b>{index}.</b> [{plabel}] {title}",
        f"💶 {html.escape(price)}",
    ]
    if loc:
        lines.append(f"📍 {html.escape(loc)}")
    if desc:
        lines.append(desc)
    if listing.url:
        lines.append(html.escape(listing.url))
    return "\n".join(lines)
