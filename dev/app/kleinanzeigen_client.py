"""Kleinanzeigen via local ebay-kleinanzeigen-api (DanielWTE)."""
from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urljoin

import requests

from config import AppConfig
from platforms import PLATFORM_KLEINANZEIGEN, composite_listing_id
from vinted import Listing

log = logging.getLogger("kleinanzeigen")


class KleinanzeigenError(RuntimeError):
    pass


class KleinanzeigenClient:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.base = (cfg.kleinanzeigen_api_url or "").rstrip("/")

    @property
    def ready(self) -> bool:
        return bool(self.base)

    def refresh_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.base = (cfg.kleinanzeigen_api_url or "").rstrip("/")

    def search(
        self,
        keyword: str,
        *,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page_count: int = 1,
    ) -> list[Listing]:
        if not self.ready:
            raise KleinanzeigenError("Kleinanzeigen API URL not set (Settings).")
        params: dict = {
            "query": keyword,
            "page_count": max(1, min(int(page_count), 3)),
        }
        if min_price is not None and min_price > 0:
            params["min_price"] = int(min_price)
        if max_price is not None and max_price > 0:
            params["max_price"] = int(max_price)

        try:
            resp = requests.get(
                f"{self.base}/inserate",
                params=params,
                timeout=90,
            )
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as exc:
            raise KleinanzeigenError(f"API request failed: {exc}") from exc

        if not payload.get("success"):
            err = payload.get("error") or payload.get("detail") or "unknown error"
            raise KleinanzeigenError(str(err))

        rows = payload.get("data") or []
        out: list[Listing] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            listing = _row_to_listing(row)
            if listing.id:
                out.append(listing)
        return out

    def fetch_detail(self, adid: str) -> Optional[dict]:
        if not self.ready or not adid:
            return None
        try:
            resp = requests.get(f"{self.base}/inserat/{adid}", timeout=60)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            log.debug("kleinanzeigen detail %s: %s", adid, exc)
            return None
        if not payload.get("success"):
            return None
        data = payload.get("data")
        return data if isinstance(data, dict) else None

    def enrich_listing(self, listing: Listing) -> Listing:
        """Load first image + full description for Telegram."""
        raw_id = listing.id.split(":", 1)[-1] if listing.id else ""
        detail = self.fetch_detail(raw_id)
        if not detail:
            return listing
        images = detail.get("images") or []
        if images and not listing.photo_url:
            listing.photo_url = str(images[0])
        desc = detail.get("description") or ""
        if desc:
            listing.description = str(desc).strip()
        price = detail.get("price") or {}
        if isinstance(price, dict) and price.get("amount"):
            try:
                listing.price = float(str(price["amount"]).replace(",", "."))
            except ValueError:
                pass
        if detail.get("title"):
            listing.title = str(detail["title"])
        return listing


def _row_to_listing(row: dict) -> Listing:
    adid = str(row.get("adid") or "").strip()
    href = str(row.get("url") or row.get("href") or "").strip()
    if href and not href.startswith("http"):
        href = urljoin("https://www.kleinanzeigen.de", href)

    price = 0.0
    raw_price = str(row.get("price") or "").strip()
    if raw_price:
        m = re.search(r"[\d.,]+", raw_price.replace(".", "").replace(",", "."))
        if m:
            try:
                price = float(m.group(0).replace(",", "."))
            except ValueError:
                price = 0.0

    title = str(row.get("title") or "").strip()
    desc = str(row.get("description") or "").strip()
    location = str(row.get("location") or row.get("ort") or "").strip()
    if isinstance(row.get("location"), dict):
        loc = row["location"]
        location = ", ".join(
            p
            for p in (
                str(loc.get("zip") or "").strip(),
                str(loc.get("city") or "").strip(),
                str(loc.get("state") or "").strip(),
            )
            if p
        )

    return Listing(
        id=composite_listing_id(PLATFORM_KLEINANZEIGEN, adid),
        title=title or "Kleinanzeigen listing",
        brand="",
        size="",
        status="",
        price=price,
        currency="EUR",
        url=href,
        photo_url="",
        description=desc,
        location=location,
        platform=PLATFORM_KLEINANZEIGEN,
        raw=row,
    )
