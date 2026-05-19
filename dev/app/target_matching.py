"""Snipe-target matching: fuzzy brands, strict product words, filters."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from categories import listing_matches_categories
from listing_utils import (
    build_target_size_keyset,
    listing_matches_size_keys,
    tokenize_keyword,
)

_BRAND_TOKENS = frozenset({
    "nike", "adidas", "jordan", "puma", "reebok", "new", "balance",
    "ralph", "lauren", "polo", "tommy", "hilfiger", "lacoste", "carhartt",
    "stone", "island", "north", "face", "patagonia", "arcteryx",
    "supreme", "stussy", "trapstar", "corteiz", "yeezy", "gucci", "prada",
    "balenciaga", "moncler", "burberry", "dior", "louis", "vuitton",
})

_FUZZY_MIN_LEN = 4
_FUZZY_RATIO = 0.82

# Must appear in listing title (not brand-only / category-style matches)
_TITLE_ONLY_PRODUCT_TOKENS = frozenset({"essentials"})


def _token_in_hay_fuzzy(token: str, hay: str) -> bool:
    if not token:
        return True
    if token in hay:
        return True
    if len(token) < _FUZZY_MIN_LEN:
        return token in hay
    for word in re.findall(r"[a-z0-9]{3,}", hay):
        if SequenceMatcher(None, token, word).ratio() >= _FUZZY_RATIO:
            return True
    return False


def relevance_score(title: str, brand: str, keyword: str) -> float:
    """
    Brand tokens: fuzzy (ralph / laurin / ralf).
    Product tokens (polo, backpack, …): must appear exactly in title/brand.
    """
    tokens = tokenize_keyword(keyword)
    if not tokens:
        return 1.0
    hay = f"{title or ''} {brand or ''}".lower()
    if not hay.strip():
        return 0.0

    brand_tokens = [t for t in tokens if t in _BRAND_TOKENS]
    product_tokens = [t for t in tokens if t not in _BRAND_TOKENS]

    if "new" in brand_tokens and "balance" in keyword.lower():
        if "new balance" not in hay and not ("new" in hay and "balance" in hay):
            return 0.0
        brand_tokens = [t for t in brand_tokens if t not in ("new", "balance")]

    for b in brand_tokens:
        if not _token_in_hay_fuzzy(b, hay):
            return 0.0

    if not product_tokens:
        return 1.0

    title_l = (title or "").lower()
    hits = 0
    for p in product_tokens:
        if p in _TITLE_ONLY_PRODUCT_TOKENS:
            if p in title_l:
                hits += 1
        elif p in hay:
            hits += 1
    if hits < len(product_tokens):
        return hits / len(product_tokens)
    return 1.0


def listing_matches_snipe_target(listing: Any, target: Any) -> bool:
    title = getattr(listing, "title", "") or ""
    brand = getattr(listing, "brand", "") or getattr(listing, "brand_title", "") or ""
    keyword = getattr(target, "keyword", "") or ""

    if relevance_score(title, brand, keyword) < 0.85:
        return False

    categories = getattr(target, "categories", None) or []
    if not listing_matches_categories(title, list(categories)):
        return False

    sizes = getattr(target, "sizes", None) or []
    mode = (getattr(target, "size_mode", None) or "any").lower()
    if not sizes or mode == "any":
        pass
    else:
        keys = build_target_size_keyset(list(sizes))
        if keys:
            listing_size = str(getattr(listing, "size", "") or "")
            matches = listing_matches_size_keys(listing_size, keys)
            if mode == "exclude" and matches:
                return False
            if mode == "include" and not matches:
                return False

    colors = getattr(target, "colors", None) or []
    if colors:
        hay = f"{title} {brand}".lower()
        if not any(c.lower().strip() in hay for c in colors if c.strip()):
            return False

    must = getattr(target, "must_include", None) or []
    if must:
        hay = f"{title} {brand}".lower()
        if not all(m.lower().strip() in hay for m in must if m.strip()):
            return False

    exclude = getattr(target, "exclude_words", None) or []
    if exclude:
        hay = f"{title} {brand}".lower()
        if any(x.lower().strip() in hay for x in exclude if x.strip()):
            return False

    return True
