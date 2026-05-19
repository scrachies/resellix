"""Playwright browser setup for Kleinanzeigen API (timeouts, Edge fallback, mirrors)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from config import APP_DIR, RUNTIME_DIR

ROOT = APP_DIR
PLAYWRIGHT_MARKER = RUNTIME_DIR / "playwright_browser_ok"
CHANNEL_FILE = RUNTIME_DIR / "playwright_channel"

# Alternate CDN if cdn.playwright.dev drops (ECONNRESET / ENOTFOUND).
DOWNLOAD_MIRRORS = (
    None,
    "https://playwright.azureedge.net",
    "https://npmmirror.com/mirrors/playwright/",
)


def _log(msg: str) -> None:
    print(msg, flush=True)


def read_playwright_channel() -> str:
    if CHANNEL_FILE.is_file():
        ch = CHANNEL_FILE.read_text(encoding="utf-8").strip().lower()
        if ch in ("msedge", "chrome", "chromium"):
            return ch
    return "chromium"


def _launch_kwargs(channel: str) -> dict:
    kwargs: dict = {"headless": True}
    if channel and channel != "chromium":
        kwargs["channel"] = channel
    return kwargs


def playwright_can_launch(channel: str | None = None) -> bool:
    channel = (channel or "chromium").lower()
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _test() -> None:
            pw = await async_playwright().start()
            try:
                browser = await pw.chromium.launch(**_launch_kwargs(channel))
                await browser.close()
            finally:
                await pw.stop()

        asyncio.run(_test())
        return True
    except Exception:
        return False


def _run_install(args: list[str], timeout_sec: int, env: dict | None = None) -> bool:
    run_env = os.environ.copy()
    run_env.setdefault("PYTHONIOENCODING", "utf-8")
    run_env.setdefault("PYTHONUTF8", "1")
    if env:
        run_env.update(env)
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "playwright", *args],
            cwd=str(ROOT),
            env=run_env,
            timeout=timeout_sec,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        _log(f"[WARN] Playwright install timed out after {timeout_sec}s: {' '.join(args)}")
        return False
    except Exception as exc:
        _log(f"[WARN] Playwright install error: {exc}")
        return False


def _mark_ready(channel: str) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    PLAYWRIGHT_MARKER.write_text("ok", encoding="utf-8")
    CHANNEL_FILE.write_text(channel, encoding="utf-8")


def ensure_playwright_browser() -> str | None:
    """
    Ensure a Playwright browser is usable. Returns channel name or None.
    On Windows prefers Microsoft Edge (no ~180MB Chromium download).
    """
    if PLAYWRIGHT_MARKER.is_file():
        channel = read_playwright_channel()
        if playwright_can_launch(channel):
            return channel
        _log("[Setup] Playwright marker stale — reinstalling browser driver…")
        PLAYWRIGHT_MARKER.unlink(missing_ok=True)

    if sys.platform == "win32":
        _log("[Setup] Playwright: Microsoft Edge (uses system browser, small download)…")
        if _run_install(["install", "msedge"], timeout_sec=180):
            if playwright_can_launch("msedge"):
                _mark_ready("msedge")
                _log("[OK] Playwright ready (Microsoft Edge).")
                return "msedge"

    _log("[Setup] Playwright Chromium (first run ~180MB; unstable networks may need a retry)…")
    for mirror in DOWNLOAD_MIRRORS:
        env = os.environ.copy()
        if mirror:
            env["PLAYWRIGHT_DOWNLOAD_HOST"] = mirror.rstrip("/")
            _log(f"[Setup] Trying download mirror: {mirror}")
        if _run_install(["install", "chromium"], timeout_sec=900, env=env):
            if playwright_can_launch("chromium"):
                _mark_ready("chromium")
                _log("[OK] Playwright ready (Chromium).")
                return "chromium"
        if mirror is None:
            _log("[WARN] Chromium download failed — retry with install_playwright.bat")

    _log(
        "[WARN] Playwright browser not installed — Kleinanzeigen disabled. "
        "Vinted and eBay still work. Run install_playwright.bat when online."
    )
    return None


def apply_playwright_env(env: dict | None = None) -> dict:
    """Set PLAYWRIGHT_CHANNEL for the Kleinanzeigen API subprocess."""
    out = dict(env or os.environ)
    if PLAYWRIGHT_MARKER.is_file():
        ch = read_playwright_channel()
        if ch != "chromium":
            out["PLAYWRIGHT_CHANNEL"] = ch
    return out
