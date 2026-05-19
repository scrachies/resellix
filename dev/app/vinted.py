"""Vinted client – uses pyVinted (herissondev/vinted-api-wrapper) by default."""
from __future__ import annotations

import json
import logging
import random
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import quote_plus

import requests

try:  # fake_useragent ships an offline fallback in recent versions
    from fake_useragent import UserAgent
    _UA = UserAgent()
except Exception:  # pragma: no cover - network/SSL fallback
    _UA = None

from config import TARGETS_PATH, AppConfig
from listing_utils import filter_relevant_listings, normalize_size_keys
from platforms import PLATFORM_VINTED, normalize_platforms
from vinted_api import build_catalog_url, host_to_tld
from pyvinted_client import diagnose as pyvinted_diagnose
from pyvinted_client import reset_client as reset_pyvinted
from pyvinted_client import search_catalog_url as pyvinted_search

log = logging.getLogger("vinted")


# ---------------------------------------------------------------------------
# Snipe targets (persisted in targets.json)
# ---------------------------------------------------------------------------

def _normalize_size_mode(raw: Any, sizes: list[str]) -> str:
    mode = str(raw or "").strip().lower()
    if mode in ("any", "include", "exclude"):
        return mode
    return "include" if sizes else "any"


def _parse_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [p.strip() for p in re.split(r"[,;]+", value) if p.strip()]
    return []


@dataclass
class SnipeTarget:
    keyword: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    expected_price: Optional[float] = None
    min_profit: Optional[float] = None
    catalog_id: Optional[int] = None
    brand_id: Optional[int] = None
    sizes: list[str] = field(default_factory=list)
    size_mode: str = "any"  # any | include | exclude
    colors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    exclude_words: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=lambda: [PLATFORM_VINTED])
    enabled: bool = True

    @property
    def label(self) -> str:
        bits = [self.keyword]
        if self.min_price is not None:
            bits.append(f">={self.min_price:.0f}")
        if self.max_price is not None:
            bits.append(f"<={self.max_price:.0f}")
        return " ".join(bits)

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "expected_price": self.expected_price,
            "min_profit": self.min_profit,
            "catalog_id": self.catalog_id,
            "brand_id": self.brand_id,
            "sizes": self.sizes,
            "size_mode": self.size_mode,
            "colors": self.colors,
            "categories": self.categories,
            "must_include": self.must_include,
            "exclude_words": self.exclude_words,
            "platforms": self.platforms,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SnipeTarget":
        return cls(
            keyword=str(data.get("keyword", "")).strip(),
            min_price=_to_float(data.get("min_price")),
            max_price=_to_float(data.get("max_price")),
            expected_price=_to_float(data.get("expected_price")),
            min_profit=_to_float(data.get("min_profit")),
            catalog_id=_to_int(data.get("catalog_id")),
            brand_id=_to_int(data.get("brand_id")),
            sizes=normalize_size_keys(_parse_str_list(data.get("sizes"))),
            size_mode=_normalize_size_mode(
                data.get("size_mode"),
                _parse_str_list(data.get("sizes")),
            ),
            colors=_parse_str_list(data.get("colors")),
            categories=_parse_str_list(data.get("categories")) or ["all"],
            must_include=_parse_str_list(data.get("must_include")),
            exclude_words=_parse_str_list(data.get("exclude_words")),
            platforms=normalize_platforms(data.get("platforms"), default=[PLATFORM_VINTED]),
            enabled=bool(data.get("enabled", True)),
        )


def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


class TargetStore:
    """Thread-safe persistent store of SnipeTargets in targets.json."""

    def __init__(self, path: Path = TARGETS_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._targets: list[SnipeTarget] = []
        self.load()

    def load(self) -> list[SnipeTarget]:
        with self._lock:
            if not self.path.exists():
                self._targets = []
                return []
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover
                log.error("Failed to read targets.json: %s", exc)
                self._targets = []
                return []
            self._targets = [SnipeTarget.from_dict(d) for d in data if d.get("keyword")]
            # Migrate plain S/M/L sizes to facet keys once
            changed = False
            for t in self._targets:
                normed = normalize_size_keys(t.sizes)
                if normed != t.sizes:
                    t.sizes = normed
                    changed = True
            if changed:
                self.path.write_text(
                    json.dumps([x.to_dict() for x in self._targets], indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            return list(self._targets)

    def save(self) -> None:
        with self._lock:
            self.path.write_text(
                json.dumps([t.to_dict() for t in self._targets], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def list(self) -> list[SnipeTarget]:
        with self._lock:
            return list(self._targets)

    def add(self, target: SnipeTarget) -> None:
        with self._lock:
            self._targets.append(target)
        self.save()

    def remove(self, index: int) -> Optional[SnipeTarget]:
        with self._lock:
            if 0 <= index < len(self._targets):
                t = self._targets.pop(index)
            else:
                return None
        self.save()
        return t

    def replace(self, index: int, target: SnipeTarget) -> bool:
        with self._lock:
            if 0 <= index < len(self._targets):
                self._targets[index] = target
            else:
                return False
        self.save()
        return True

    def toggle(self, index: int) -> Optional[SnipeTarget]:
        with self._lock:
            if 0 <= index < len(self._targets):
                self._targets[index].enabled = not self._targets[index].enabled
                t = self._targets[index]
            else:
                return None
        self.save()
        return t


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class VintedError(RuntimeError):
    """Base error for Vinted API failures."""


class VintedAuthError(VintedError):
    """Session / auth failure."""


class VintedRateLimit(VintedError):
    """HTTP 429."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class Listing:
    id: str
    title: str
    brand: str = ""
    size: str = ""
    status: str = ""           # condition (e.g. "Sehr gut")
    price: float = 0.0
    currency: str = "EUR"
    url: str = ""
    photo_url: str = ""
    description: str = ""
    location: str = ""
    platform: str = PLATFORM_VINTED
    raw: dict = field(default_factory=dict)


def _extract_size(raw: dict) -> str:
    for key in ("size_title", "size"):
        val = raw.get(key) or ""
        if isinstance(val, str) and val.strip():
            return val.strip()
    item_size = raw.get("item_size")
    if isinstance(item_size, dict):
        t = item_size.get("title") or item_size.get("name") or ""
        if t:
            return str(t).strip()
    if isinstance(item_size, str) and item_size.strip():
        return item_size.strip()
    size_id = raw.get("size_id") or raw.get("size_id_text")
    if isinstance(size_id, str) and size_id.strip():
        return size_id.strip()
    return ""


def _extract_location(raw: dict) -> str:
    for key in ("city", "city_title", "location", "location_title"):
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    user = raw.get("user")
    if isinstance(user, dict):
        for key in ("city", "city_title", "location"):
            val = user.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


def _extract_photo_url(raw: dict, fallback_photo: str = "") -> str:
    photo = (fallback_photo or "").strip()
    if photo:
        return photo
    p = raw.get("photo") or {}
    if isinstance(p, dict):
        for key in ("full_size_url", "url", "thumb_url"):
            u = p.get(key)
            if u:
                return str(u)
        hr = p.get("high_resolution") or {}
        if isinstance(hr, dict) and hr.get("url"):
            return str(hr["url"])
    photos = raw.get("photos") or []
    if photos and isinstance(photos[0], dict):
        p0 = photos[0]
        for key in ("full_size_url", "url", "thumb_url"):
            u = p0.get(key)
            if u:
                return str(u)
    return ""


def _item_to_listing(item: Any, host: str) -> Listing:
    """Map pyVinted Item → our Listing."""
    raw = getattr(item, "raw_data", None) or {}
    if not isinstance(raw, dict):
        raw = {}

    url = str(getattr(item, "url", "") or "")
    if url.startswith("/"):
        url = f"https://{host}{url}"

    status = str(raw.get("status", "") or raw.get("status_title", "") or "").strip()

    return Listing(
        id=str(getattr(item, "id", "")),
        title=str(getattr(item, "title", "") or "").strip(),
        brand=str(getattr(item, "brand_title", "") or raw.get("brand_title", "") or "").strip(),
        size=_extract_size(raw),
        status=status,
        price=float(getattr(item, "price", 0) or 0),
        currency=str(getattr(item, "currency", "EUR") or "EUR"),
        url=url,
        photo_url=_extract_photo_url(raw, str(getattr(item, "photo", "") or "")),
        description=str(raw.get("description", "") or "").strip()[:500],
        location=_extract_location(raw),
        raw=raw,
    )


class VintedClient:
    """Builds catalog URLs and searches via pyVinted (herissondev)."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def refresh_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        reset_pyvinted()

    def search(
        self,
        keyword: str,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        per_page: int = 20,
        order: str = "newest_first",
        sort: Optional[str] = None,
        catalog_id: Optional[int] = None,
        brand_id: Optional[int] = None,
    ) -> list[Listing]:
        vinted_order = order
        if sort == "oldest":
            vinted_order = "oldest_first"
        elif sort == "cheapest":
            vinted_order = "price_low_to_high"
        elif sort == "expensive":
            vinted_order = "price_high_to_low"
        elif sort == "newest":
            vinted_order = "newest_first"

        catalog_url = build_catalog_url(
            self.cfg.vinted_host,
            search_text=keyword,
            min_price=min_price,
            max_price=max_price,
            order=vinted_order,
            brand_id=brand_id,
            catalog_id=catalog_id,
            per_page=per_page,
            page=1,
        )
        listings = self.search_url(catalog_url, per_page=per_page)
        return filter_relevant_listings(listings, keyword)

    def search_url(self, catalog_url: str, per_page: int = 20) -> list[Listing]:
        """Same as pyVinted: vinted.items.search(catalog_url, nbrItems, page)."""
        host = self.cfg.vinted_host
        if not host.startswith("www."):
            host = f"www.vinted.{host_to_tld(host)}"

        try:
            items = pyvinted_search(self.cfg, catalog_url, per_page=per_page, page=1)
        except Exception as exc:
            err = str(exc).lower()
            if "429" in err:
                raise VintedRateLimit("Vinted rate-limited (429).") from exc
            if "401" in err or "403" in err or "cookie" in err:
                raise VintedAuthError(
                    f"{exc}\n\nPaste _vinted_de_session in Settings if this keeps failing."
                ) from exc
            raise VintedError(str(exc)) from exc

        listings = [_item_to_listing(it, host) for it in items]
        # Parse keyword from catalog URL for relevance filter
        kw = ""
        if "search_text=" in catalog_url:
            import re as _re
            from urllib.parse import unquote as _uq

            m = _re.search(r"search_text=([^&]+)", catalog_url)
            if m:
                kw = _uq(m.group(1).replace("+", " "))
        if kw:
            listings = filter_relevant_listings(listings, kw)
        return listings

    def run_diagnose(self) -> list[str]:
        return pyvinted_diagnose(self.cfg)


def _parse_listing(item: dict, host: str) -> Listing:
    price_obj = item.get("price") or {}
    if isinstance(price_obj, dict):
        amount = price_obj.get("amount") or price_obj.get("price") or 0
        currency = price_obj.get("currency_code") or "EUR"
    else:  # older API returned a flat number
        amount = price_obj
        currency = item.get("currency", "EUR")

    url = item.get("url") or ""
    if url and url.startswith("/"):
        url = f"https://{host}{url}"
    if not url and item.get("id"):
        url = f"https://{host}/items/{item['id']}"

    return Listing(
        id=str(item.get("id", "")),
        title=str(item.get("title", "")).strip(),
        brand=str(item.get("brand_title", "")).strip(),
        size=_extract_size(item),
        status=str(item.get("status", "") or item.get("status_title", "")).strip(),
        price=_to_float(amount) or 0.0,
        currency=str(currency),
        url=url,
        photo_url=_extract_photo_url(item),
        raw=item,
    )


# ---------------------------------------------------------------------------
# Resale estimates — product-specific (longest phrase wins)
# ---------------------------------------------------------------------------

# (search phrase, typical resale EUR) — sorted longest-first at runtime
_PRODUCT_RESALE_EUR: list[tuple[str, float]] = [
    ("nike elite backpack", 55),
    ("nike elite tracksuit", 75),
    ("nike elite", 60),
    ("nike tech fleece", 45),
    ("nike tn", 50),
    ("nike dunk low", 80),
    ("dunk low", 75),
    ("jordan 4", 120),
    ("jordan 1", 100),
    ("air jordan 4", 120),
    ("adidas samba", 55),
    ("new balance 550", 65),
    ("yeezy 350", 140),
    ("yeezy slide", 45),
    ("stone island badge", 90),
    ("stone island sweatshirt", 110),
    ("stone island", 120),
    ("carhartt detroit jacket", 55),
    ("carhartt detroit", 50),
    ("carhartt jacket", 45),
    ("the north face nuptse", 120),
    ("the north face", 70),
    ("ralph lauren cable knit", 45),
    ("ralph lauren pullover", 35),
    ("polo ralph lauren", 40),
    ("tommy hilfiger jacket", 45),
    ("tommy hilfiger hoodie", 28),
    ("tommy hilfiger polo", 22),
    ("tommy hilfiger", 30),
    ("lacoste polo", 28),
    ("trapstar puffer", 90),
    ("trapstar hoodie", 55),
    ("corteiz tracksuit", 70),
    ("corteiz hoodie", 55),
    ("arcteryx jacket", 200),
    ("patagonia fleece", 55),
    ("supreme hoodie", 120),
    ("moncler jacket", 280),
    ("backpack", 40),
    ("tracksuit", 50),
    ("hoodie", 35),
    ("pullover", 30),
    ("sneaker", 55),
    ("trainer", 50),
    ("ralph lauren", 35),
    ("nike", 40),
    ("jordan", 90),
    ("adidas", 35),
    ("lacoste", 30),
    ("carhartt", 45),
    ("trapstar", 70),
    ("corteiz", 60),
    ("yeezy", 120),
    ("new balance", 60),
]

_PRODUCT_RESALE_SORTED = sorted(_PRODUCT_RESALE_EUR, key=lambda x: -len(x[0]))


def _baseline_from_text(haystack: str) -> float:
    best = 0.0
    for phrase, value in _PRODUCT_RESALE_SORTED:
        if phrase in haystack and value > best:
            best = value
    return best


_KIDS_RE = re.compile(
    r"\b(baby|beb[eé]|bébé|kinder|kind|enfant|enfants|child|children|"
    r"kids|toddler|newborn|nouveau.?n[eé]|fillette?|gar[cç]on|"
    r"\d+\s*-\s*\d+\s*monate|\d+\s*m\b|\d+\s*months?)\b",
    re.I,
)


def is_kids_listing(title: str, size: str = "") -> bool:
    blob = f"{title} {size}"
    return bool(_KIDS_RE.search(blob))


def estimate_resale_eur(
    listing: Listing,
    keyword: str = "",
    market_median: Optional[float] = None,
) -> float:
    hay = f"{listing.brand} {listing.title}".lower()
    kw = (keyword or "").lower().strip()

    from_keyword = _baseline_from_text(kw) if kw else 0.0
    from_listing = _baseline_from_text(hay)
    from_market = market_median * 1.08 if market_median and market_median > 0 else 0.0

    base = max(from_keyword, from_listing, from_market)
    price = float(listing.price or 0)

    if is_kids_listing(listing.title, listing.size):
        if price > 0:
            return min(base, price * 2.0, price + 12.0)
        return min(base, 18.0)

    return base


def compute_match_profit(
    listing: Listing,
    target: Optional[SnipeTarget],
) -> tuple[Optional[float], Optional[float]]:
    """
    Returns (estimated_resale, profit) — profit is None when estimate is not trustworthy.
  User-set expected_price on target is always trusted.
    """
    if not target:
        return None, None

    price = float(listing.price or 0)
    if price <= 0:
        return None, None

    if target.expected_price and target.expected_price > 0:
        est = float(target.expected_price)
        profit = est - price
        return est, profit if profit > 0 else None

    est = estimate_resale_eur(listing, keyword=target.keyword)
    if est <= 0 or est <= price:
        return None, None

    profit = est - price
    max_profit = max(15.0, price * 1.8)
    if is_kids_listing(listing.title, listing.size):
        max_profit = min(max_profit, 12.0)
    if profit > max_profit:
        return None, None

    if profit > price * 2.5:
        return None, None

    return est, profit


def deal_score(listing: Listing, expected_eur: float | None = None) -> float:
    """Return a 0..1 'cheapness' score (1 == roughly free, 0 == not a deal)."""
    expected = expected_eur if expected_eur and expected_eur > 0 else estimate_resale_eur(listing)
    if expected <= 0 or listing.price <= 0:
        return 0.0
    saving_ratio = max(0.0, (expected - listing.price) / expected)
    return min(1.0, saving_ratio)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def random_sleep_seconds(cfg: AppConfig) -> float:
    lo = max(8, int(cfg.poll_min_seconds))
    hi = max(lo + 1, int(cfg.poll_max_seconds))
    return random.uniform(lo, hi)


def sleep_between_targets_seconds() -> float:
    """Short pause between target scans to reduce burst rate-limits."""
    return random.uniform(1.0, 2.0)


def build_search_url(host: str, keyword: str, max_price: Optional[float] = None) -> str:
    return build_catalog_url(
        host, search_text=keyword, max_price=max_price, order="newest_first"
    )
