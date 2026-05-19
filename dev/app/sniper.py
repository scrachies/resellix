"""Background sniper: polls Vinted, Kleinanzeigen, eBay."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import database as db
from config import AppConfig
from ebay_client import EbayClient, EbayError
from kleinanzeigen_client import KleinanzeigenClient, KleinanzeigenError
from notifier import TelegramNotifier
from platforms import (
    PLATFORM_EBAY,
    PLATFORM_KLEINANZEIGEN,
    PLATFORM_VINTED,
    platform_label,
)
from target_matching import listing_matches_snipe_target
from vinted import (
    Listing,
    SnipeTarget,
    TargetStore,
    VintedAuthError,
    VintedClient,
    VintedError,
    VintedRateLimit,
    compute_match_profit,
    random_sleep_seconds,
    sleep_between_targets_seconds,
)

log = logging.getLogger("sniper")


@dataclass
class MatchEvent:
    listing: Listing
    target: SnipeTarget
    profit: Optional[float]
    estimated_resale: Optional[float] = None

    def to_dict(self) -> dict:
        est, profit = compute_match_profit(self.listing, self.target)
        if self.estimated_resale is not None:
            est = self.estimated_resale
        if self.profit is not None:
            profit = self.profit
        return {
            "listing_id": self.listing.id,
            "target_label": self.target.keyword,
            "platform": getattr(self.listing, "platform", PLATFORM_VINTED),
            "title": self.listing.title,
            "brand": self.listing.brand,
            "size": self.listing.size,
            "status": self.listing.status,
            "price": self.listing.price,
            "currency": self.listing.currency,
            "expected_price": float(est or 0.0),
            "profit": float(profit or 0.0),
            "url": self.listing.url,
            "photo_url": self.listing.photo_url,
            "description": getattr(self.listing, "description", "") or "",
        }


LogCallback = Callable[[str], None]
MatchCallback = Callable[[MatchEvent], None]
StatusCallback = Callable[[dict], None]


class Sniper:
    def __init__(
        self,
        cfg: AppConfig,
        targets: TargetStore,
        notifier: Optional[TelegramNotifier] = None,
    ) -> None:
        self.cfg = cfg
        self.targets = targets
        self.notifier = notifier
        self.vinted = VintedClient(cfg)
        self.kleinanzeigen = KleinanzeigenClient(cfg)
        self.ebay = EbayClient(cfg)
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_log: Optional[LogCallback] = None
        self.on_match: Optional[MatchCallback] = None
        self.on_status: Optional[StatusCallback] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="Sniper", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def pause(self, paused: bool = True) -> None:
        if paused:
            self._pause.set()
        else:
            self._pause.clear()

    @property
    def paused(self) -> bool:
        return self._pause.is_set()

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def refresh_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.vinted.refresh_config(cfg)
        self.kleinanzeigen.refresh_config(cfg)
        self.ebay.refresh_config(cfg)
        if self.notifier:
            self.notifier.refresh(cfg)

    def _log(self, msg: str) -> None:
        log.info(msg)
        if self.on_log:
            try:
                self.on_log(msg)
            except Exception:
                pass

    def _push_status(self, **kwargs) -> None:
        if self.on_status:
            try:
                self.on_status(kwargs)
            except Exception:
                pass

    def _active_platforms(self, target: SnipeTarget) -> list[str]:
        global_enabled = set(self.cfg.sniper_platforms or [])
        target_set = set(target.platforms or [PLATFORM_VINTED])
        return [p for p in (PLATFORM_VINTED, PLATFORM_KLEINANZEIGEN, PLATFORM_EBAY) if p in global_enabled and p in target_set]

    def _run(self) -> None:
        self._log("Sniper thread started.")
        while not self._stop.is_set():
            if self._pause.is_set():
                time.sleep(2)
                continue

            targets = [t for t in self.targets.list() if t.enabled]
            if not targets:
                self._push_status(next_in=10, action="idle - no targets")
                self._sleep(10)
                continue

            for i, target in enumerate(targets):
                if self._stop.is_set() or self._pause.is_set():
                    break
                platforms = self._active_platforms(target)
                if not platforms:
                    self._log(f"No platforms enabled for '{target.keyword}' — check Settings.")
                    continue
                for pi, platform in enumerate(platforms):
                    if self._stop.is_set() or self._pause.is_set():
                        break
                    self._scan_target(target, platform)
                    if pi + 1 < len(platforms) and not self._stop.is_set():
                        self._sleep(sleep_between_targets_seconds())
                if i + 1 < len(targets) and not self._stop.is_set():
                    self._sleep(sleep_between_targets_seconds())

            wait = random_sleep_seconds(self.cfg)
            self._push_status(next_in=int(wait), action="cooling down")
            self._sleep(wait)

        self._log("Sniper thread stopped.")

    def _sleep(self, seconds: float) -> None:
        end = time.time() + seconds
        while time.time() < end and not self._stop.is_set():
            time.sleep(min(1.0, end - time.time()))

    def _fetch_listings(self, target: SnipeTarget, platform: str) -> list[Listing]:
        if platform == PLATFORM_VINTED:
            if not self.cfg.vinted_ready:
                raise VintedAuthError("Vinted not configured")
            return self.vinted.search(
                keyword=target.keyword,
                min_price=target.min_price,
                max_price=target.max_price,
                catalog_id=target.catalog_id,
                brand_id=target.brand_id,
            )
        if platform == PLATFORM_KLEINANZEIGEN:
            if not self.kleinanzeigen.ready:
                raise KleinanzeigenError("Kleinanzeigen API URL missing in Settings")
            return self.kleinanzeigen.search(
                keyword=target.keyword,
                min_price=target.min_price,
                max_price=target.max_price,
                page_count=1,
            )
        if platform == PLATFORM_EBAY:
            return self.ebay.search(
                keyword=target.keyword,
                min_price=target.min_price,
                max_price=target.max_price,
            )
        return []

    def _scan_target(self, target: SnipeTarget, platform: str) -> None:
        plabel = platform_label(platform)
        try:
            listings = self._fetch_listings(target, platform)
        except VintedAuthError as exc:
            self._log(f"Vinted auth: {exc}")
            return
        except VintedRateLimit:
            self._log("Vinted rate limited — sleeping 90s")
            self._sleep(90)
            return
        except VintedError as exc:
            self._log(f"Vinted error [{target.keyword}]: {exc}")
            return
        except KleinanzeigenError as exc:
            self._log(f"Kleinanzeigen error [{target.keyword}]: {exc}")
            return
        except EbayError as exc:
            self._log(f"eBay error [{target.keyword}]: {exc}")
            return
        except Exception as exc:
            self._log(f"Error [{plabel} / {target.keyword}]: {exc}")
            return

        new_count = 0
        match_count = 0

        for listing in listings:
            db.bump_stat("listings_checked")
            if not listing.id or db.is_listing_seen(listing.id):
                continue

            if not listing_matches_snipe_target(listing, target):
                continue

            db.mark_listing_seen(listing.id, target_label=target.keyword)
            new_count += 1

            if target.min_price is not None and listing.price < target.min_price:
                continue
            if target.max_price is not None and listing.price > target.max_price:
                continue

            est, profit = compute_match_profit(listing, target)

            if target.min_profit is not None and target.min_profit > 0:
                if profit is None or profit < target.min_profit:
                    continue

            if platform == PLATFORM_KLEINANZEIGEN and not listing.photo_url:
                try:
                    listing = self.kleinanzeigen.enrich_listing(listing)
                except Exception as exc:
                    log.debug("Kleinanzeigen enrich: %s", exc)

            event = MatchEvent(
                listing=listing,
                target=target,
                profit=profit,
                estimated_resale=est,
            )
            db.record_match(event.to_dict())
            db.bump_stat("matches_sent")
            match_count += 1

            extra = ""
            if profit is not None:
                extra = f" (+{profit:.0f}€ est.)"
            self._log(
                f"MATCH [{plabel}] [{target.keyword}] {listing.title} — "
                f"{listing.price:.2f} {listing.currency}{extra}"
            )

            if self.on_match:
                try:
                    self.on_match(event)
                except Exception as exc:
                    log.warning("on_match callback failed: %s", exc)

            if self.notifier and self.notifier.enabled:
                try:
                    self.notifier.send_match(listing, target, profit)
                except Exception as exc:
                    log.warning("Telegram notification failed: %s", exc)

        self._log(
            f"Scanned {plabel} '{target.keyword}': {len(listings)} hits, "
            f"{new_count} new relevant, {match_count} alerts."
        )
