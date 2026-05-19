"""Telegram interactive search mode (pauses sniper alerts until 'continue')."""
from __future__ import annotations

import asyncio
import html
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

from telegram import Update
from telegram.ext import ContextTypes

from adhoc_search import AdhocSearchRequest, run_adhoc_search
from platforms import ALL_PLATFORMS, normalize_platforms, platform_label
from search_query import (
    ParsedSearchQuery,
    format_price_range,
    looks_like_search_request,
    parse_search_text,
)
from search_results_format import format_search_result_block
from search_sort import SORT_LABELS, SORT_NEWEST, parse_sort_reply

if TYPE_CHECKING:
    from config import AppConfig
    from sniper import Sniper

log = logging.getLogger("tg-search")


class SearchStep(str, Enum):
    PLATFORM = "platform"
    COUNT = "count"
    SORT = "sort"
    CONTINUE = "continue"


@dataclass
class SearchSession:
    query: ParsedSearchQuery
    step: SearchStep = SearchStep.PLATFORM
    platforms: list[str] = field(default_factory=list)
    limit: int = 10
    sort: str = SORT_NEWEST
    paused_sniper: bool = False


def parse_platform_reply(text: str) -> Optional[list[str]]:
    t = (text or "").strip().lower()
    if not t:
        return None
    if t in ("all", "everywhere", "überall", "uberal", "alle", "every", "0"):
        return list(ALL_PLATFORMS)
    if t in ("1", "vinted", "v"):
        return ["vinted"]
    if t in ("2", "kleinanzeigen", "ka", "klein"):
        return ["kleinanzeigen"]
    if t in ("3", "ebay", "e"):
        return ["ebay"]
    return normalize_platforms(t.replace(" und ", ",").replace(" and ", ","))


def parse_count_reply(text: str) -> Optional[int]:
    t = (text or "").strip()
    m = re.match(r"^(\d+)\s*$", t)
    if not m:
        return None
    n = int(m.group(1))
    if 1 <= n <= 25:
        return n
    return None


class TelegramSearchMode:
    def __init__(self, cfg: "AppConfig", sniper: Optional["Sniper"] = None) -> None:
        self.cfg = cfg
        self.sniper = sniper
        self._sessions: dict[int, SearchSession] = {}

    def has_session(self, chat_id: int) -> bool:
        return chat_id in self._sessions

    def clear_session(self, chat_id: int, resume: bool = True) -> None:
        session = self._sessions.pop(chat_id, None)
        if resume and session and session.paused_sniper and self.sniper:
            self.sniper.pause(False)

    def begin_search(self, chat_id: int, query: ParsedSearchQuery) -> SearchSession:
        self.clear_session(chat_id, resume=True)
        paused = False
        if self.sniper and self.sniper.running and not self.sniper.paused:
            self.sniper.pause(True)
            paused = True
        session = SearchSession(query=query, paused_sniper=paused)
        self._sessions[chat_id] = session
        return session

    async def handle_message(
        self,
        update: Update,
        ctx: ContextTypes.DEFAULT_TYPE,
        text: str,
    ) -> bool:
        if not update.message or not update.effective_chat:
            return False
        chat_id = update.effective_chat.id
        stripped = (text or "").strip()

        if stripped.lower() in ("/cancel", "cancel", "abbrechen"):
            if self.has_session(chat_id):
                self.clear_session(chat_id, resume=True)
                await update.message.reply_text(
                    "Search cancelled. Sniper alerts resumed."
                )
                return True
            return False

        if self.has_session(chat_id):
            session = self._sessions[chat_id]
            if session.step == SearchStep.CONTINUE:
                if stripped.lower() in ("continue", "weiter", "resume", "fortsetzen", "go"):
                    self.clear_session(chat_id, resume=True)
                    await update.message.reply_text(
                        "✅ Sniper alerts resumed. You will get match notifications again."
                    )
                    return True
                if looks_like_search_request(stripped):
                    parsed = parse_search_text(stripped)
                    if parsed:
                        session = self.begin_search(chat_id, parsed)
                        await self._ask_platform(update, session)
                        return True
                await update.message.reply_html(
                    "Still in search mode. Type <code>continue</code> to resume sniper alerts, "
                    "or <code>cancel</code> to abort."
                )
                return True
            await self._advance_session(update, session, stripped)
            return True

        if looks_like_search_request(stripped):
            parsed = parse_search_text(stripped)
            if not parsed:
                await update.message.reply_text(
                    "Could not parse search. Examples:\n"
                    "• search for raspberry pi under 40 over 20\n"
                    "• search for item min 20 max 40\n"
                    "• search for item between 30 and 50"
                )
                return True
            session = self.begin_search(chat_id, parsed)
            await self._ask_platform(update, session)
            return True

        return False

    async def start_from_command(self, update: Update, raw: str) -> None:
        parsed = parse_search_text(raw if raw.strip() else "/search")
        if not parsed:
            await update.message.reply_html(
                "<b>Usage</b>\n"
                "<code>/search raspberry pi under 40 over 20</code>\n"
                "<code>/search item min 20 max 40</code>\n"
                "<code>/search item between 30 and 50</code>"
            )
            return
        chat_id = update.effective_chat.id
        session = self.begin_search(chat_id, parsed)
        await self._ask_platform(update, session)

    async def _ask_platform(self, update: Update, session: SearchSession) -> None:
        q = session.query
        price = format_price_range(q.min_price, q.max_price)
        await update.message.reply_html(
            f"🔍 <b>Search mode</b> — sniper alerts paused.\n\n"
            f"<b>Query:</b> {html.escape(q.keyword)}\n"
            f"<b>Price:</b> {html.escape(price)}\n\n"
            "Where should I search?\n"
            "• <code>vinted</code> or <code>1</code>\n"
            "• <code>kleinanzeigen</code> or <code>2</code>\n"
            "• <code>ebay</code> or <code>3</code>\n"
            "• <code>everywhere</code> or <code>all</code>"
        )

    async def _ask_sort(self, update: Update, session: SearchSession) -> None:
        await update.message.reply_html(
            "Sort results how?\n"
            "• <code>1</code> or <code>newest</code>\n"
            "• <code>2</code> or <code>oldest</code>\n"
            "• <code>3</code> or <code>cheapest</code>\n"
            "• <code>4</code> or <code>expensive</code>"
        )

    async def _advance_session(
        self,
        update: Update,
        session: SearchSession,
        text: str,
    ) -> None:
        if session.step == SearchStep.PLATFORM:
            platforms = parse_platform_reply(text)
            if not platforms:
                await update.message.reply_text(
                    "Please reply: vinted, kleinanzeigen, ebay, or everywhere"
                )
                return
            session.platforms = platforms
            session.step = SearchStep.COUNT
            names = ", ".join(platform_label(p) for p in platforms)
            await update.message.reply_html(
                f"Platform: <b>{html.escape(names)}</b>\n\n"
                "How many results total? (1–25, default 10)"
            )
            return

        if session.step == SearchStep.COUNT:
            n = parse_count_reply(text)
            if n is None and text.strip().lower() in ("", "default", "ok"):
                n = 10
            if n is None:
                await update.message.reply_text("Send a number from 1 to 25.")
                return
            session.limit = n
            session.step = SearchStep.SORT
            await self._ask_sort(update, session)
            return

        if session.step == SearchStep.SORT:
            sort = parse_sort_reply(text)
            if not sort:
                await update.message.reply_text(
                    "Reply with: newest, oldest, cheapest, or expensive (or 1–4)."
                )
                return
            session.sort = sort
            await update.message.reply_text(
                f"Searching ({SORT_LABELS.get(sort, sort)})… can take up to a minute."
            )
            await self._run_and_reply(update, session)

    async def _run_and_reply(self, update: Update, session: SearchSession) -> None:
        q = session.query
        req = AdhocSearchRequest(
            keyword=q.keyword,
            min_price=q.min_price,
            max_price=q.max_price,
            platforms=session.platforms,
            limit=session.limit,
            sort=session.sort,
        )
        loop = asyncio.get_running_loop()
        try:
            results, errors = await loop.run_in_executor(
                None, lambda: run_adhoc_search(self.cfg, req)
            )
        except Exception as exc:
            log.exception("search failed")
            await update.message.reply_text(f"Search failed: {exc}")
            session.step = SearchStep.CONTINUE
            return

        sort_label = SORT_LABELS.get(session.sort, session.sort)
        lines = [
            f"🔍 <b>{html.escape(q.keyword)}</b> — "
            f"{html.escape(format_price_range(q.min_price, q.max_price))}",
            f"<i>{html.escape(sort_label)} · {len(results)} result(s)</i>",
            "",
        ]
        if not results:
            lines.append("<i>No listings found in that price range.</i>")
        for i, (platform, listing) in enumerate(results, 1):
            lines.append(format_search_result_block(i, platform, listing))
            lines.append("")

        if errors:
            lines.append("<i>Notes:</i> " + html.escape("; ".join(errors)))

        session.step = SearchStep.CONTINUE
        body = "\n".join(lines)
        if len(body) > 4000:
            await update.message.reply_html(body[:3990] + "\n…")
            await update.message.reply_html(
                "<i>Results truncated — lower the count next time.</i>"
            )
        else:
            await update.message.reply_html(body, disable_web_page_preview=False)
        await update.message.reply_html(
            "Type <code>continue</code> to resume sniper match notifications."
        )
