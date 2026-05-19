"""eBay.de search (HTML) — independent from Kleinanzeigen."""
from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup

from config import AppConfig
from platforms import PLATFORM_EBAY, composite_listing_id
from vinted import Listing

log = logging.getLogger("ebay")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class EbayError(RuntimeError):
    pass


class EbayClient:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        host = (cfg.ebay_host or "www.ebay.de").strip().lstrip(".")
        self.base = f"https://{host}"

    def refresh_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        host = (cfg.ebay_host or "www.ebay.de").strip().lstrip(".")
        self.base = f"https://{host}"

    @property
    def ready(self) -> bool:
        return bool(self.base)

    def search(
        self,
        keyword: str,
        *,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort: Optional[str] = None,
    ) -> list[Listing]:
        if not keyword.strip():
            return []

        from search_sort import ebay_sop_for_sort

        params = {"_nkw": keyword.strip(), "_sop": ebay_sop_for_sort(sort or "newest")}
        if min_price is not None and min_price > 0:
            params["_udlo"] = str(int(min_price))
        if max_price is not None and max_price > 0:
            params["_udhi"] = str(int(max_price))

        url = f"{self.base}/sch/i.html"
        try:
            resp = requests.get(
                url,
                params=params,
                headers={
                    "User-Agent": _UA,
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=25,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise EbayError(f"eBay search failed: {exc}") from exc

        return self._parse_search_html(resp.text, keyword)

    def _parse_search_html(self, html: str, keyword: str) -> list[Listing]:
        found = _parse_json_items(html)
        if found:
            return found

        soup = BeautifulSoup(html, "lxml")
        out: list[Listing] = []
        seen: set[str] = set()

        for li in soup.select("li.s-item, li.s-card"):
            link = li.select_one("a.s-item__link, a[href*='/itm/']")
            if not link:
                continue
            href = (link.get("href") or "").split("?")[0]
            if not href or "/itm/" not in href:
                continue
            m = re.search(r"/itm/(\d+)", href)
            item_id = m.group(1) if m else href
            cid = composite_listing_id(PLATFORM_EBAY, item_id)
            if cid in seen:
                continue
            seen.add(cid)

            title_el = li.select_one(
                ".s-item__title, .s-card__title, [class*='item__title']"
            )
            title = title_el.get_text(" ", strip=True) if title_el else ""
            title = re.sub(r"^Neu:\s*", "", title, flags=re.I).strip()
            if not title or "shop on ebay" in title.lower():
                continue

            price_el = li.select_one(".s-item__price, .s-card__price")
            price = _parse_price(price_el.get_text() if price_el else "")

            img_el = li.select_one("img.s-item__image-img, img[src]")
            photo = ""
            if img_el:
                photo = img_el.get("src") or img_el.get("data-src") or ""
                if photo.startswith("//"):
                    photo = "https:" + photo

            subtitle = li.select_one(".s-item__subtitle, .s-item__details")
            desc = subtitle.get_text(" ", strip=True) if subtitle else ""
            loc_el = li.select_one(".s-item__location, .s-item__itemLocation")
            location = loc_el.get_text(" ", strip=True) if loc_el else ""

            out.append(
                Listing(
                    id=cid,
                    title=title,
                    brand="",
                    size="",
                    status="",
                    price=price,
                    currency="EUR",
                    url=href if href.startswith("http") else urljoin(self.base, href),
                    photo_url=photo,
                    description=desc,
                    location=location,
                    platform=PLATFORM_EBAY,
                    raw={"keyword": keyword},
                )
            )
            if len(out) >= 40:
                break
        return out


def _parse_price(text: str) -> float:
    if not text:
        return 0.0
    t = text.replace("\xa0", " ").strip()
    m = re.search(r"([\d.,]+)", t)
    if not m:
        return 0.0
    num = m.group(1)
    if "," in num and "." in num:
        num = num.replace(".", "").replace(",", ".")
    elif "," in num:
        num = num.replace(",", ".")
    try:
        return float(num)
    except ValueError:
        return 0.0


def _parse_json_items(html: str) -> list[Listing]:
    """Try embedded JSON (eBay sometimes ships item arrays in script tags)."""
    markers = ('"itemId"', '"itemWebUrl"')
    if not any(m in html for m in markers):
        return []

    out: list[Listing] = []
    seen: set[str] = set()
    for item_id in re.findall(r'"itemId"\s*:\s*"(\d+)"', html):
        cid = composite_listing_id(PLATFORM_EBAY, item_id)
        if cid in seen:
            continue
        seen.add(cid)

        title_m = re.search(
            rf'"itemId"\s*:\s*"{re.escape(item_id)}"[^}}]*?"title"\s*:\s*"([^"]+)"',
            html,
        )
        title = title_m.group(1) if title_m else f"eBay item {item_id}"
        url_m = re.search(
            rf'"itemId"\s*:\s*"{re.escape(item_id)}"[^}}]*?"itemWebUrl"\s*:\s*"([^"]+)"',
            html,
        )
        url = (url_m.group(1).replace("\\u002F", "/") if url_m else f"https://www.ebay.de/itm/{item_id}")

        price = 0.0
        price_m = re.search(
            rf'"itemId"\s*:\s*"{re.escape(item_id)}"[^}}]*?"value"\s*:\s*([\d.]+)',
            html,
        )
        if price_m:
            try:
                price = float(price_m.group(1))
            except ValueError:
                pass

        img_m = re.search(
            rf'"itemId"\s*:\s*"{re.escape(item_id)}"[^}}]*?"imageUrl"\s*:\s*"([^"]+)"',
            html,
        )
        photo = img_m.group(1).replace("\\u002F", "/") if img_m else ""

        out.append(
            Listing(
                id=cid,
                title=title,
                price=price,
                currency="EUR",
                url=url,
                photo_url=photo,
                platform=PLATFORM_EBAY,
            )
        )
        if len(out) >= 40:
            break
    return out
