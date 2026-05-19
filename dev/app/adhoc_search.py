"""One-shot marketplace search (Telegram browse mode — no snipe targets / seen DB)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from config import AppConfig
from ebay_client import EbayClient, EbayError
from kleinanzeigen_client import KleinanzeigenClient, KleinanzeigenError
from platforms import (
    ALL_PLATFORMS,
    PLATFORM_EBAY,
    PLATFORM_KLEINANZEIGEN,
    PLATFORM_VINTED,
    normalize_platforms,
    platform_label,
)
from search_sort import SORT_CHEAPEST, SORT_EXPENSIVE, SORT_NEWEST, SORT_OLDEST
from vinted import Listing, VintedAuthError, VintedClient, VintedError, VintedRateLimit

log = logging.getLogger("adhoc_search")


@dataclass
class AdhocSearchRequest:
    keyword: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    platforms: list[str] | None = None
    limit: int = 10
    sort: str = SORT_NEWEST


def _in_price_range(
    price: float,
    min_p: Optional[float],
    max_p: Optional[float],
) -> bool:
    if min_p is not None and price < min_p - 0.01:
        return False
    if max_p is not None and price > max_p + 0.01:
        return False
    return True


def _fetch_platform(
    cfg: AppConfig,
    platform: str,
    req: AdhocSearchRequest,
    per_page: int,
) -> list[Listing]:
    if platform == PLATFORM_VINTED:
        if not cfg.vinted_ready:
            raise VintedAuthError("Vinted not configured (cookie in Settings).")
        client = VintedClient(cfg)
        return client.search(
            keyword=req.keyword,
            min_price=req.min_price,
            max_price=req.max_price,
            per_page=per_page,
            sort=req.sort,
        )
    if platform == PLATFORM_KLEINANZEIGEN:
        client = KleinanzeigenClient(cfg)
        if not client.ready:
            raise KleinanzeigenError("Kleinanzeigen API not running (start.bat / Settings).")
        return client.search(
            keyword=req.keyword,
            min_price=req.min_price,
            max_price=req.max_price,
            page_count=2,
        )
    if platform == PLATFORM_EBAY:
        return EbayClient(cfg).search(
            keyword=req.keyword,
            min_price=req.min_price,
            max_price=req.max_price,
            sort=req.sort,
        )
    return []


def _apply_sort(merged: list[tuple[str, Listing]], sort: str) -> list[tuple[str, Listing]]:
    if sort == SORT_CHEAPEST:
        return sorted(merged, key=lambda x: x[1].price)
    if sort == SORT_EXPENSIVE:
        return sorted(merged, key=lambda x: x[1].price, reverse=True)
    if sort == SORT_OLDEST:
        return list(reversed(merged))
    return merged


def _enrich_for_display(cfg: AppConfig, results: list[tuple[str, Listing]]) -> None:
    """Fill description/location for Kleinanzeigen (and KA list rows)."""
    ka = KleinanzeigenClient(cfg)
    for i, (platform, listing) in enumerate(results):
        if platform != PLATFORM_KLEINANZEIGEN:
            if not listing.description and (listing.brand or listing.size):
                listing.description = " · ".join(
                    p for p in (listing.brand, listing.size, listing.status) if p
                )
            continue
        try:
            enriched = ka.enrich_listing(listing)
            results[i] = (platform, enriched)
            detail = ka.fetch_detail(listing.id.split(":", 1)[-1])
            if detail:
                loc = detail.get("location")
                if isinstance(loc, dict):
                    city = str(loc.get("city") or "").strip()
                    state = str(loc.get("state") or "").strip()
                    zip_code = str(loc.get("zip") or "").strip()
                    parts = [p for p in (zip_code, city, state) if p]
                    if parts:
                        enriched.location = ", ".join(parts)
                elif isinstance(loc, str) and loc.strip():
                    enriched.location = loc.strip()
        except Exception as exc:
            log.debug("enrich %s: %s", listing.id, exc)


def run_adhoc_search(cfg: AppConfig, req: AdhocSearchRequest) -> tuple[list[tuple[str, Listing]], list[str]]:
    """
    Returns (results, errors).
    results: list of (platform_id, listing) sorted per req.sort, capped at req.limit.
    """
    platforms = normalize_platforms(req.platforms, default=list(ALL_PLATFORMS))
    global_enabled = set(cfg.sniper_platforms or ALL_PLATFORMS)
    platforms = [p for p in platforms if p in global_enabled]
    try:
        from subscription import filter_platforms

        platforms = filter_platforms(platforms)
    except Exception:
        pass
    if not platforms:
        return [], ["No platforms enabled in Settings."]

    limit = max(1, min(int(req.limit or 10), 25))
    per_page = min(40, max(20, limit * 3))

    merged: list[tuple[str, Listing]] = []
    errors: list[str] = []

    for platform in platforms:
        plabel = platform_label(platform)
        try:
            rows = _fetch_platform(cfg, platform, req, per_page)
        except VintedAuthError as exc:
            errors.append(f"{plabel}: {exc}")
            continue
        except VintedRateLimit:
            errors.append(f"{plabel}: rate limited — try again shortly.")
            continue
        except (VintedError, KleinanzeigenError, EbayError) as exc:
            errors.append(f"{plabel}: {exc}")
            continue
        except Exception as exc:
            log.exception("adhoc search %s", platform)
            errors.append(f"{plabel}: {exc}")
            continue

        for listing in rows:
            if not listing.id or listing.price <= 0:
                continue
            if not _in_price_range(listing.price, req.min_price, req.max_price):
                continue
            merged.append((platform, listing))

    merged = _apply_sort(merged, req.sort or SORT_NEWEST)

    seen_urls: set[str] = set()
    unique: list[tuple[str, Listing]] = []
    for platform, listing in merged:
        url = (listing.url or "").strip()
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append((platform, listing))
        if len(unique) >= limit:
            break

    _enrich_for_display(cfg, unique)
    return unique, errors
