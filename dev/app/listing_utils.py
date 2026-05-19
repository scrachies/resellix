"""Sort, filter, relevance scoring, and resale estimates for listings."""
from __future__ import annotations

import re
import statistics
from typing import Any, Callable, Optional

_BRAND_TOKENS = frozenset({
    "nike", "adidas", "jordan", "puma", "reebok", "new", "balance",
    "ralph", "lauren", "polo", "tommy", "hilfiger", "lacoste", "carhartt",
    "stone", "island", "north", "face", "patagonia", "arcteryx",
    "supreme", "stussy", "trapstar", "corteiz", "yeezy", "gucci", "prada",
    "balenciaga", "moncler", "burberry", "dior", "lv", "louis", "vuitton",
    "uniqlo", "zara", "h&m", "essentials", "fear", "god", "asics", "salomon",
    "vans", "converse", "timberland", "ugg", "birkenstock",
})

_STOPWORDS = frozenset({
    "and", "or", "the", "a", "an", "mit", "und", "der", "die", "das", "snipe",
})

LETTER_SIZES = ("XXS", "XS", "S", "M", "L", "XL", "XXL", "2XL", "3XL", "4XL")

SORT_LABELS: list[tuple[str, str]] = [
    ("newest", "Newest first"),
    ("oldest", "Oldest first"),
    ("price_low", "Price: low → high"),
    ("price_high", "Price: high → low"),
    ("deal_best", "Best discount %"),
]

CHEAP_DEAL_QUERIES: list[tuple[str, float]] = [
    ("nike elite backpack", 28),
    ("nike elite tracksuit", 40),
    ("nike tech fleece", 22),
    ("nike tn", 25),
    ("jordan 4", 55),
    ("jordan 1", 50),
    ("dunk low", 45),
    ("adidas samba", 30),
    ("new balance 550", 35),
    ("ralph lauren pullover", 15),
    ("polo ralph lauren", 18),
    ("stone island badge", 45),
    ("carhartt detroit jacket", 25),
    ("the north face nuptse", 45),
    ("tommy hilfiger jacket", 22),
    ("lacoste polo", 15),
    ("trapstar hoodie", 30),
    ("corteiz tracksuit", 35),
]

TREND_VINTED_QUERIES: list[str] = [
    "nike elite backpack",
    "nike elite tracksuit",
    "nike tech fleece",
    "jordan 4",
    "dunk low",
    "adidas samba",
    "stone island sweatshirt",
    "carhartt detroit",
    "ralph lauren cable knit",
    "the north face nuptse",
    "new balance 550",
    "yeezy slide",
    "corteiz hoodie",
    "trapstar puffer",
]


def tokenize_keyword(keyword: str) -> list[str]:
    raw = re.findall(r"[a-z0-9]+", (keyword or "").lower())
    return [t for t in raw if len(t) > 1 and t not in _STOPWORDS]


def filter_relevant_listings(listings: list[Any], keyword: str, min_score: float = 0.65) -> list[Any]:
    from target_matching import relevance_score

    if not keyword or not listings:
        return listings
    scored: list[tuple[float, Any]] = []
    for item in listings:
        title = getattr(item, "title", "") or ""
        brand = getattr(item, "brand", "") or getattr(item, "brand_title", "") or ""
        s = relevance_score(title, brand, keyword)
        if s >= min_score:
            scored.append((s, item))
    scored.sort(key=lambda x: -x[0])
    return [it for _, it in scored]


def listing_price(item: Any) -> float:
    return float(getattr(item, "price", 0) or 0)


def median_listing_price(listings: list[Any]) -> float:
    prices = sorted(p for p in (listing_price(x) for x in listings) if p > 0)
    if not prices:
        return 0.0
    return float(statistics.median(prices))


def sort_key_fn(mode: str) -> Callable[[dict], Any]:
    if mode == "oldest":
        return lambda r: int(r.get("created_ts") or 0)
    if mode == "price_low":
        return lambda r: float(r.get("price") or 0)
    if mode == "price_high":
        return lambda r: -float(r.get("price") or 0)
    if mode == "deal_best":
        return lambda r: -float(r.get("score") or 0)
    return lambda r: -int(r.get("created_ts") or 0)


def sort_rows(rows: list[dict], mode: str) -> list[dict]:
    return sorted(rows, key=sort_key_fn(mode or "newest"))


def filter_rows_by_platform(rows: list[dict], selected: set[str]) -> list[dict]:
    if not selected:
        return rows
    return [r for r in rows if (r.get("platform") or "vinted") in selected]


def filter_rows_by_target(rows: list[dict], target_label: str) -> list[dict]:
    if not target_label or target_label in ("All", "All targets"):
        return rows
    return [r for r in rows if (r.get("target_label") or "") == target_label]


# ---------------------------------------------------------------------------
# Size parsing & multi-select filter
# ---------------------------------------------------------------------------


def parse_size_facets(size_str: str) -> set[str]:
    """Normalized facets for matching (letter:m, num:42, waist:32, raw)."""
    if not size_str:
        return set()
    s = re.sub(r"\s+", " ", size_str.strip())
    facets: set[str] = {f"raw:{s.lower()}"}

    for letter in LETTER_SIZES:
        if re.search(rf"(?:^|[\s/|·\-–,]){re.escape(letter)}(?:[\s/|·\-–,]|$)", s, re.I):
            facets.add(f"letter:{letter.lower()}")

    for n in re.findall(r"\b(\d{2,3})\b", s):
        facets.add(f"num:{n}")

    wm = re.search(r"\bW\s*(\d{1,2})\b", s, re.I)
    if wm:
        facets.add(f"waist:{wm.group(1)}")

    lm = re.search(r"\bL\s*(\d{1,2})\b", s, re.I)
    if lm and wm:
        facets.add(f"len:{lm.group(1)}")

    return facets


def primary_size_keys(facets: set[str]) -> set[str]:
    """Keys used for filter checkboxes (one per logical size)."""
    keys: set[str] = set()
    for f in facets:
        if f.startswith(("letter:", "num:", "waist:")):
            keys.add(f)
    if not keys and facets:
        for f in facets:
            if f.startswith("raw:"):
                keys.add(f)
    return keys


def size_option_label(facet_key: str, sample_raw: str = "") -> str:
    if facet_key.startswith("letter:"):
        return facet_key.split(":", 1)[1].upper()
    if facet_key.startswith("num:"):
        return f"EU {facet_key.split(':', 1)[1]}"
    if facet_key.startswith("waist:"):
        w = facet_key.split(":", 1)[1]
        return f"W{w}"
    if sample_raw:
        return sample_raw[:28]
    return facet_key


def size_options_from_rows(rows: list[dict]) -> list[tuple[str, str]]:
    """Build filter options: (facet_key, display_label), sorted."""
    key_to_sample: dict[str, str] = {}
    for r in rows:
        raw = str(r.get("size") or "").strip()
        if not raw or raw == "—":
            continue
        for key in primary_size_keys(parse_size_facets(raw)):
            key_to_sample.setdefault(key, raw)

    def sort_key(item: tuple[str, str]) -> tuple:
        k, _ = item
        if k.startswith("letter:"):
            order = {x.lower(): i for i, x in enumerate(LETTER_SIZES)}
            return (0, order.get(k.split(":")[1], 99), k)
        if k.startswith("num:"):
            return (1, int(k.split(":")[1]), k)
        if k.startswith("waist:"):
            return (2, int(k.split(":")[1]), k)
        return (3, k)

    items = [(k, size_option_label(k, key_to_sample[k])) for k in key_to_sample]
    return sorted(items, key=sort_key)


def normalize_size_keys(sizes: list[str]) -> list[str]:
    """Convert UI labels (S, M) or facet keys (letter:m) to facet keys."""
    keys: set[str] = set()
    for raw in sizes:
        sk = str(raw).strip()
        if not sk:
            continue
        if ":" in sk:
            keys.add(sk.lower())
        else:
            keys.update(primary_size_keys(parse_size_facets(sk)))
    return sorted(keys)


def build_target_size_keyset(sizes: list[str]) -> set[str]:
    return set(normalize_size_keys(sizes))


def listing_matches_size_keys(listing_size: str, selected_keys: set[str]) -> bool:
    if not selected_keys:
        return True
    listing_keys = primary_size_keys(parse_size_facets(listing_size))
    return bool(listing_keys & selected_keys)


def filter_rows_by_size_keys(rows: list[dict], selected_keys: set[str]) -> list[dict]:
    if not selected_keys:
        return rows
    return [
        r for r in rows
        if listing_matches_size_keys(str(r.get("size") or ""), selected_keys)
    ]


def enrich_match_row(row: dict, targets_by_kw: dict[str, Any] | None = None) -> dict:
    from vinted import Listing, compute_match_profit

    price = float(row.get("price") or 0)
    title = row.get("title") or ""
    brand = row.get("brand") or ""
    kw = row.get("target_label") or ""
    target = (targets_by_kw or {}).get(kw)

    listing = Listing(
        id=str(row.get("listing_id") or ""),
        title=title,
        brand=brand,
        size=str(row.get("size") or ""),
        price=price,
        currency=str(row.get("currency") or "EUR"),
    )

    est, profit = compute_match_profit(listing, target) if target else (None, None)
    if est is None:
        est = float(row.get("expected_price") or 0) or None
    if profit is None:
        p = float(row.get("profit") or 0)
        profit = p if p > 0 else None

    out = dict(row)
    out["estimated_resale"] = est or 0.0
    out["profit"] = profit or 0.0
    out["profit_confident"] = profit is not None and profit > 0
    return out


def is_cheap_listing(
    price: float,
    expected_resale: float,
    *,
    max_price: float,
    min_discount_ratio: float = 0.40,
) -> bool:
    if price <= 0 or expected_resale <= 0:
        return False
    if max_price > 0 and price > max_price:
        return False
    saving = (expected_resale - price) / expected_resale
    return saving >= min_discount_ratio
