"""Telegram command interface (python-telegram-bot v20+, async).

Commands:
  /start             - greeting + help
  /help              - command reference
  /search <query>    - interactive search (pauses sniper until "continue")
  /add <spec>        - add a snipe target
  /list              - show active snipe targets
  /remove <index>    - remove a target (1-based)
  /toggle <index>    - enable/disable a target
  /trends            - run an on-demand trend scan
  /status            - uptime + counts
  /cancel            - abort search mode and resume alerts

Free text examples:
  search for nike dunk under 20 eur but over 15
"""
from __future__ import annotations

import asyncio
import html
import logging
import re
import time
from typing import TYPE_CHECKING, Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import database as db
from config import AppConfig
from trends import format_trends, save_trends, scan_trends
from platforms import normalize_platforms
from telegram_search import TelegramSearchMode
from vinted import SnipeTarget, TargetStore

if TYPE_CHECKING:
    from sniper import Sniper

log = logging.getLogger("tg-bot")


def _finalize_size_mode(mode: str, sizes: list[str]) -> str:
    if not sizes:
        return "any"
    if mode in ("exclude", "include"):
        return mode
    return "include"


def _parse_add_args(raw: str) -> Optional[SnipeTarget]:
    """Parse `keyword | max:20 | sizes:M,L | colors:navy | exclude:baby`."""
    if not raw.strip():
        return None
    parts = [p.strip() for p in raw.split("|")]
    keyword = parts[0].strip()
    if not keyword:
        return None
    min_price = max_price = expected_price = min_profit = None
    sizes: list[str] = []
    size_mode = "any"
    colors: list[str] = []
    categories: list[str] = []
    exclude_words: list[str] = []
    platforms: list[str] = []

    for chunk in parts[1:]:
        m = re.match(r"\s*([a-zA-Z_]+)\s*[:=]\s*(.+)\s*$", chunk, re.I)
        if not m:
            continue
        k = m.group(1).lower()
        v = m.group(2).strip()
        if k in ("sizes", "size"):
            sizes = [x.strip() for x in re.split(r"[,;]+", v) if x.strip()]
            size_mode = "include"
            continue
        if k in ("exclude_sizes", "exclude_size"):
            sizes = [x.strip() for x in re.split(r"[,;]+", v) if x.strip()]
            size_mode = "exclude"
            continue
        if k in ("size_mode", "sizes_mode"):
            m = v.strip().lower()
            if m in ("any", "all", "include", "only", "exclude"):
                size_mode = "include" if m == "only" else ("any" if m in ("any", "all") else m)
            continue
        if k in ("colors", "colour", "color"):
            colors = [x.strip() for x in re.split(r"[,;]+", v) if x.strip()]
            continue
        if k in ("exclude", "exclude_words"):
            exclude_words = [x.strip() for x in re.split(r"[,;]+", v) if x.strip()]
            continue
        if k in ("categories", "category", "type"):
            categories = [x.strip().lower() for x in re.split(r"[,;]+", v) if x.strip()]
            continue
        if k in ("platforms", "platform"):
            platforms = normalize_platforms(v)
            continue
        num = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*$", v)
        if not num:
            continue
        val = float(num.group(1))
        if k in ("min", "minprice", "price_min"):
            min_price = val
        elif k in ("max", "maxprice", "price", "price_max"):
            max_price = val
        elif k in ("profit", "minprofit"):
            min_profit = val
        elif k in ("expect", "expected", "sell"):
            expected_price = val

    return SnipeTarget(
        keyword=keyword,
        min_price=min_price,
        max_price=max_price,
        expected_price=expected_price,
        min_profit=min_profit,
        sizes=sizes,
        size_mode=_finalize_size_mode(size_mode, sizes),
        colors=colors,
        categories=categories or ["all"],
        exclude_words=exclude_words,
        platforms=platforms or ["vinted"],
    )


class ResellTelegramBot:
    """Long-poll Telegram bot. Runs inside its own asyncio loop in a thread."""

    HELP_TEXT = (
        "<b>Resellix</b>\n"
        "\n"
        "<b>/search</b>  <code>nike dunk under 20 but over 15</code>\n"
        "  e.g. <code>search for pi under 40 over 20</code>, "
        "<code>min 20 max 40</code>, <code>between 30 and 50</code>\n"
        "  (platform → count → sort → results; type <code>continue</code> after)\n"
        "\n"
        "<b>/add</b>  <code>keyword | max:20 | platforms:vinted,ebay</code>\n"
        "<b>/list</b>          - show active snipe targets\n"
        "<b>/remove</b> <i>n</i>     - remove target n\n"
        "<b>/toggle</b> <i>n</i>     - pause/resume target n\n"
        "<b>/trends</b>        - on-demand trend scan\n"
        "<b>/status</b>        - uptime + counters\n"
        "<b>/cancel</b>        - abort search mode\n"
    )

    def __init__(
        self,
        cfg: AppConfig,
        targets: TargetStore,
        start_ts: float,
        sniper: Optional["Sniper"] = None,
    ) -> None:
        self.cfg = cfg
        self.targets = targets
        self.start_ts = start_ts
        self.sniper = sniper
        self.search_mode = TelegramSearchMode(cfg, sniper)
        self.app: Optional[Application] = None

    def _authorized(self, update: Update) -> bool:
        cid = (self.cfg.telegram_chat_id or "").strip()
        if not cid or not update.effective_chat:
            return True
        try:
            expected = int(cid)
        except ValueError:
            return str(update.effective_chat.id) == cid
        return update.effective_chat.id == expected

    # ------------------------------------------------------------------

    def build_app(self) -> Application:
        app = ApplicationBuilder().token(self.cfg.telegram_bot_token).build()
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("search", self._cmd_search))
        app.add_handler(CommandHandler("cancel", self._cmd_cancel))
        app.add_handler(CommandHandler("add", self._cmd_add))
        app.add_handler(CommandHandler("list", self._cmd_list))
        app.add_handler(CommandHandler("remove", self._cmd_remove))
        app.add_handler(CommandHandler("toggle", self._cmd_toggle))
        app.add_handler(CommandHandler("trends", self._cmd_trends))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_text)
        )
        self.app = app
        return app

    # ------- handlers --------------------------------------------------

    async def _cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        await update.message.reply_html(
            "Resellix is online.\n\n" + self.HELP_TEXT
        )

    async def _cmd_help(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        await update.message.reply_html(self.HELP_TEXT)

    async def _cmd_search(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        raw = " ".join(ctx.args) if ctx.args else ""
        await self.search_mode.start_from_command(update, raw)

    async def _cmd_cancel(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        if update.effective_chat:
            self.search_mode.clear_session(update.effective_chat.id, resume=True)
        await update.message.reply_text("Search cancelled. Sniper alerts resumed.")

    async def _on_text(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update) or not update.message:
            return
        text = update.message.text or ""
        await self.search_mode.handle_message(update, ctx, text)

    async def _cmd_add(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        raw = " ".join(ctx.args) if ctx.args else ""
        target = _parse_add_args(raw)
        if target is None:
            await update.message.reply_html(
                "Usage: <code>/add keyword | max:20 | profit:5 | expect:60</code>"
            )
            return
        self.targets.add(target)
        await update.message.reply_html(
            f"✅ Added target: <b>{html.escape(target.keyword)}</b>"
            + (f"  (max {target.max_price:.0f})" if target.max_price else "")
        )

    async def _cmd_list(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        targets = self.targets.list()
        if not targets:
            await update.message.reply_text("No snipe targets configured. Try /add.")
            return
        lines = ["<b>Active snipe targets:</b>"]
        for i, t in enumerate(targets, 1):
            mark = "🟢" if t.enabled else "⏸"
            extras = []
            if t.min_price is not None:
                extras.append(f"min {t.min_price:.0f}")
            if t.max_price is not None:
                extras.append(f"max {t.max_price:.0f}")
            if t.expected_price is not None:
                extras.append(f"expect {t.expected_price:.0f}")
            if t.min_profit is not None:
                extras.append(f"min-profit {t.min_profit:.0f}")
            extra = (" - " + ", ".join(extras)) if extras else ""
            lines.append(f"{mark} <b>{i}.</b> {html.escape(t.keyword)}{extra}")
        await update.message.reply_html("\n".join(lines))

    async def _cmd_remove(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        if not ctx.args:
            await update.message.reply_text("Usage: /remove <n>")
            return
        try:
            idx = int(ctx.args[0]) - 1
        except ValueError:
            await update.message.reply_text("Usage: /remove <n>")
            return
        removed = self.targets.remove(idx)
        if removed is None:
            await update.message.reply_text("Index out of range.")
        else:
            n = db.delete_matches_for_target(removed.keyword)
            extra = f" ({n} feed items cleared)" if n else ""
            await update.message.reply_html(
                f"🗑 Removed: <b>{html.escape(removed.keyword)}</b>{extra}"
            )

    async def _cmd_toggle(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        if not ctx.args:
            await update.message.reply_text("Usage: /toggle <n>")
            return
        try:
            idx = int(ctx.args[0]) - 1
        except ValueError:
            await update.message.reply_text("Usage: /toggle <n>")
            return
        t = self.targets.toggle(idx)
        if t is None:
            await update.message.reply_text("Index out of range.")
        else:
            state = "🟢 enabled" if t.enabled else "⏸ paused"
            await update.message.reply_html(
                f"{state}: <b>{html.escape(t.keyword)}</b>"
            )

    async def _cmd_trends(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        await update.message.reply_text("🔎 Scanning trends, give me ~20 seconds...")
        loop = asyncio.get_running_loop()
        try:
            results = await loop.run_in_executor(None, scan_trends, self.cfg)
            save_trends(results)
            txt = format_trends(results)
        except Exception as exc:
            log.exception("trend scan failed")
            await update.message.reply_text(f"Trend scan failed: {exc}")
            return
        await update.message.reply_html(f"<pre>{html.escape(txt)}</pre>")

    async def _cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._authorized(update):
            return
        up = int(time.time() - self.start_ts)
        hours, rem = divmod(up, 3600)
        minutes, _ = divmod(rem, 60)
        checked = db.get_stat("listings_checked")
        matches = db.get_stat("matches_sent")
        targets = len(self.targets.list())
        sniper_line = ""
        if self.sniper:
            state = "paused" if self.sniper.paused else "running"
            sniper_line = f"\n🎯 Sniper: {state}"
        await update.message.reply_html(
            "<b>Status</b>\n"
            f"⏱ Uptime: {hours}h {minutes}m\n"
            f"🎯 Targets: {targets}\n"
            f"👀 Listings checked: {checked}\n"
            f"📨 Matches sent: {matches}"
            f"{sniper_line}"
        )

    # ------- lifecycle -------------------------------------------------

    async def run_forever(self) -> None:
        app = self.build_app()
        await app.initialize()
        await app.start()
        if app.updater is not None:
            await app.updater.start_polling(drop_pending_updates=True)
        log.info("Telegram bot polling started.")
        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            if app.updater is not None:
                await app.updater.stop()
            await app.stop()
            await app.shutdown()
