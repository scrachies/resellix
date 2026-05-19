"""Thread bridges: Sniper -> Qt signals, Trend scan -> Qt signals."""
from __future__ import annotations

import logging
import random
import threading
import time
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from config import AppConfig
from listing_utils import (
    CHEAP_DEAL_QUERIES,
    filter_relevant_listings,
    is_cheap_listing,
    median_listing_price,
)
from sniper import MatchEvent, Sniper, SnipeTarget
from trends import TrendResult, save_trends, scan_trends

log = logging.getLogger("dashboard.workers")


class SniperBridge(QObject):
    log_message = pyqtSignal(str)
    match_found = pyqtSignal(object)
    status_update = pyqtSignal(dict)

    def __init__(self, sniper: Sniper) -> None:
        super().__init__()
        self.sniper = sniper
        sniper.on_log = self._on_log
        sniper.on_match = self._on_match
        sniper.on_status = self._on_status

    def _on_log(self, msg: str) -> None:
        self.log_message.emit(msg)

    def _on_match(self, event: MatchEvent) -> None:
        self.match_found.emit(event)

    def _on_status(self, payload: dict) -> None:
        self.status_update.emit(payload)


class TrendScanThread(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, cfg: AppConfig, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.cfg = cfg

    def run(self) -> None:
        try:
            results = scan_trends(self.cfg, progress_cb=self.progress.emit)
            try:
                save_trends(results)
            except Exception:
                pass
            self.finished_ok.emit(results)
        except Exception as exc:
            log.exception("trend scan thread failed")
            self.failed.emit(str(exc))


class CheapDealsThread(QThread):
    """Find genuinely underpriced listings (not just hyped items in a price band)."""

    progress = pyqtSignal(str)
    deals_ready = pyqtSignal(list)  # list[tuple[listing, expected, score, keyword]]
    finished_ok = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, cfg: AppConfig, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self._stop = threading.Event()

    def request_stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        from vinted import VintedClient, estimate_resale_eur, deal_score
        from vinted import VintedAuthError, VintedRateLimit, VintedError

        client = VintedClient(self.cfg)
        collected: list[tuple[object, float, float, str]] = []
        seen_ids: set[str] = set()

        for keyword, max_price in CHEAP_DEAL_QUERIES:
            if self._stop.is_set():
                break
            self.progress.emit(f"'{keyword}' — checking Vinted median…")
            try:
                listings = client.search(keyword=keyword, per_page=36)
            except VintedAuthError as exc:
                self.failed.emit(str(exc))
                return
            except VintedRateLimit:
                self.progress.emit("Rate-limited; pausing 45s…")
                time.sleep(45)
                continue
            except VintedError as exc:
                self.progress.emit(f"Skip: {exc}")
                continue
            except Exception as exc:
                self.progress.emit(f"Error: {exc}")
                continue

            relevant = filter_relevant_listings(listings, keyword)
            med = median_listing_price(relevant)

            for listing in relevant:
                lid = str(getattr(listing, "id", "") or "")
                if lid and lid in seen_ids:
                    continue
                price = float(getattr(listing, "price", 0) or 0)
                expected = estimate_resale_eur(
                    listing, keyword=keyword, market_median=med
                )
                if not is_cheap_listing(
                    price, expected, max_price=max_price, min_discount_ratio=0.38
                ):
                    continue
                score = deal_score(listing, expected)
                if score < 0.30:
                    continue
                if lid:
                    seen_ids.add(lid)
                collected.append((listing, expected, score, keyword))

            time.sleep(random.uniform(1.0, 2.0))

        collected.sort(key=lambda x: -x[2])
        self.deals_ready.emit(collected)
        self.finished_ok.emit(len(collected))


class DashboardScanThread(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(
        self,
        cfg: AppConfig,
        targets: list[SnipeTarget],
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.targets = targets

    def run(self) -> None:
        from vinted import VintedClient, VintedAuthError, VintedError

        client = VintedClient(self.cfg)
        total = 0
        try:
            for t in self.targets:
                if not t.enabled:
                    continue
                self.progress.emit(f"Scanning: {t.keyword}…")
                try:
                    listings = client.search(
                        keyword=t.keyword,
                        min_price=t.min_price,
                        max_price=t.max_price,
                        per_page=20,
                    )
                except VintedAuthError as exc:
                    self.failed.emit(str(exc))
                    return
                except VintedError as exc:
                    self.progress.emit(f"Skip {t.keyword}: {exc}")
                    continue
                total += len(listings)
            self.finished_ok.emit(total)
        except Exception as exc:
            self.failed.emit(str(exc))


class TrendDrilldownThread(QThread):
    progress = pyqtSignal(str)
    deals_ready = pyqtSignal(list)
    finished_ok = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, cfg: AppConfig, trend_name: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        self.trend_name = trend_name

    def run(self) -> None:
        from vinted import VintedClient, estimate_resale_eur, deal_score
        from vinted import VintedAuthError, VintedError

        client = VintedClient(self.cfg)
        query = self.trend_name.strip()
        self.progress.emit(f"Loading '{query}'…")
        try:
            listings = client.search(keyword=query, per_page=36, order="newest_first")
        except VintedAuthError as exc:
            self.failed.emit(str(exc))
            return
        except VintedError as exc:
            self.failed.emit(str(exc))
            return

        relevant = filter_relevant_listings(listings, query)
        med = median_listing_price(relevant)
        found: list[tuple[object, float, float, str]] = []

        for listing in relevant:
            price = float(getattr(listing, "price", 0) or 0)
            expected = estimate_resale_eur(listing, keyword=query, market_median=med)
            if not is_cheap_listing(price, expected, max_price=med * 0.75, min_discount_ratio=0.30):
                continue
            score = deal_score(listing, expected)
            if score >= 0.25:
                found.append((listing, expected, score, query))

        found.sort(key=lambda x: -x[2])
        self.deals_ready.emit(found)
        self.finished_ok.emit(len(found))


class TelegramThread(QThread):
    started_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, telegram_bot, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.bot = telegram_bot

    def run(self) -> None:
        import asyncio
        try:
            asyncio.run(self.bot.run_forever())
            self.started_ok.emit()
        except Exception as exc:
            log.exception("telegram thread crashed")
            self.failed.emit(str(exc))
