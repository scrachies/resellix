"""Telegram alerts — one photo + caption per match."""
from __future__ import annotations

import html
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests

from config import AppConfig
from platforms import platform_label
from vinted import Listing, SnipeTarget, compute_match_profit

log = logging.getLogger("notifier")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="TelegramSend")


class TelegramNotifier:
    """Sends one Telegram message per match: photo with listing caption."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    @property
    def enabled(self) -> bool:
        return bool(
            self.cfg.telegram_enabled
            and self.cfg.telegram_bot_token
            and self.cfg.telegram_chat_id
        )

    def refresh(self, cfg: AppConfig) -> None:
        self.cfg = cfg

    def send_match(
        self,
        listing: Listing,
        target: SnipeTarget,
        profit: Optional[float] = None,
    ) -> None:
        if not self.enabled:
            return
        _executor.submit(self._deliver_match, listing, target, profit)

    def send_text(self, text: str) -> None:
        if not self.enabled:
            return
        _executor.submit(_send_message_sync, self.cfg, text)

    def _deliver_match(
        self,
        listing: Listing,
        target: SnipeTarget,
        profit: Optional[float],
    ) -> None:
        title_short = (listing.title or "?")[:60]
        try:
            est, profit_out = compute_match_profit(listing, target)
            if profit is not None:
                profit_out = profit
            caption = _format_caption(listing, target, est, profit_out)
            data = _download_photo(listing.photo_url)
            if data:
                _send_photo_sync(self.cfg, data, caption)
            else:
                _send_message_sync(self.cfg, caption)
            log.info("Telegram sent: %s", title_short)
        except Exception as exc:
            log.warning("Telegram failed (%s): %s", title_short, exc)


def _api_base(cfg: AppConfig) -> str:
    return f"https://api.telegram.org/bot{cfg.telegram_bot_token}"


def _send_message_sync(cfg: AppConfig, text: str) -> None:
    """Fallback when photo download fails."""
    resp = requests.post(
        f"{_api_base(cfg)}/sendMessage",
        json={
            "chat_id": cfg.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if not resp.ok:
        raise RuntimeError(f"sendMessage {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()


def _send_photo_sync(cfg: AppConfig, photo_bytes: bytes, caption: str) -> None:
    resp = requests.post(
        f"{_api_base(cfg)}/sendPhoto",
        data={
            "chat_id": cfg.telegram_chat_id,
            "caption": caption[:1024],
            "parse_mode": "HTML",
        },
        files={"photo": ("listing.jpg", photo_bytes)},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"sendPhoto {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()


def _download_photo(url: str) -> Optional[bytes]:
    if not url:
        return None
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": _UA,
                "Accept": "image/*,*/*;q=0.8",
                "Referer": "https://www.vinted.de/",
            },
            timeout=(5, 20),
        )
        resp.raise_for_status()
        if len(resp.content) < 400:
            return None
        return resp.content
    except Exception as exc:
        log.debug("photo download: %s", exc)
        return None


def _format_caption(
    listing: Listing,
    target: SnipeTarget,
    estimated_resale: Optional[float],
    profit: Optional[float],
) -> str:
    title = html.escape(listing.title or "Listing")
    brand = html.escape(listing.brand or "—")
    size = html.escape(listing.size or "—")
    status = html.escape(listing.status or "—")
    cur = html.escape(listing.currency or "EUR")
    price = f"{listing.price:.2f} {cur}"
    link = listing.url or ""

    plat = platform_label(getattr(listing, "platform", "vinted"))
    desc = html.escape((getattr(listing, "description", "") or "").strip())
    if len(desc) > 500:
        desc = desc[:497] + "…"

    lines = [
        f"<b>{title}</b>",
        f"<i>{plat}</i>",
    ]
    if brand and brand != "—":
        lines.append(brand)
    line2 = f"{price}"
    if size and size != "—":
        line2 += f"  ·  Size {size}"
    if status and status != "—":
        line2 += f"  ·  {status}"
    lines.append(line2)
    if desc:
        lines.extend(["", desc])
    lines.append("")
    if target.expected_price and target.expected_price > 0:
        lines.append(f"Target sell  <b>{target.expected_price:.2f} {cur}</b>")
    elif estimated_resale is not None and estimated_resale > 0:
        lines.append(f"Est. resale  <b>{estimated_resale:.2f} {cur}</b>")
    if profit is not None and profit > 0:
        lines.append(f"Est. profit  <b>+{profit:.2f} {cur}</b>")
    lines.append("")
    if link:
        lines.append(f'<a href="{html.escape(link, quote=True)}">Open on Vinted</a>')
    return "\n".join(lines)
