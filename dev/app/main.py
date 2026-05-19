"""Entry point: launches the PyQt6 dashboard (which boots everything else).

Usage:
    python main.py            # opens the dashboard (recommended)
    python main.py --headless # runs without UI (sniper + Telegram bot only)
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from logging.handlers import RotatingFileHandler

from config import DEV_DIR, LOG_PATH, ensure_env_file, load_config

STARTUP_LOG = DEV_DIR / "startup_error.log"


def setup_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    try:
        fh = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handlers.append(fh)
    except Exception:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def run_headless() -> int:
    """Pure CLI runner: sniper + telegram bot, no PyQt6 dependency required."""
    import asyncio
    import threading

    from notifier import TelegramNotifier
    from sniper import Sniper
    from telegram_bot import ResellTelegramBot
    from vinted import TargetStore

    cfg = load_config()
    targets = TargetStore()
    notifier = TelegramNotifier(cfg)
    sniper = Sniper(cfg, targets, notifier)
    sniper.start()

    stop_evt = threading.Event()

    def _signal_handler(*_):
        stop_evt.set()

    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    if cfg.telegram_enabled:
        bot = ResellTelegramBot(cfg, targets, time.time(), sniper=sniper)
        def _tg():
            try:
                asyncio.run(bot.run_forever())
            except Exception as exc:
                logging.error("telegram bot crashed: %s", exc)
        threading.Thread(target=_tg, daemon=True, name="TelegramThread").start()

    logging.info("Headless mode running. Press Ctrl+C to exit.")
    try:
        while not stop_evt.is_set():
            time.sleep(1)
    finally:
        sniper.stop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Resellix")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without UI (sniper + Telegram bot only)",
    )
    args = parser.parse_args()

    setup_logging()
    ensure_env_file()

    if args.headless:
        return run_headless()

    try:
        from dashboard.app import run_dashboard
    except ImportError as exc:
        logging.error(
            "PyQt6 is not installed (%s). Either run `pip install -r requirements.txt` "
            "or pass --headless.",
            exc,
        )
        return 2
    return run_dashboard()


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            STARTUP_LOG.write_text(tb, encoding="utf-8")
        except Exception:
            pass
        print(tb, file=sys.stderr)
        if sys.platform in ("win32", "darwin") and not getattr(sys, "frozen", False):
            try:
                input("\nError — press Enter to close...")
            except EOFError:
                pass
        code = 1
    else:
        code = code or 0
    sys.exit(code)
