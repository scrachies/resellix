"""Centralised configuration — all user data lives in dev/."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, set_key

from platforms import normalize_platforms

APP_DIR: Path = Path(__file__).resolve().parent
DEV_DIR: Path = APP_DIR.parent
ROOT_DIR: Path = DEV_DIR.parent  # install root (windows / apple / dev / README only)

ENV_PATH: Path = DEV_DIR / ".env"
TARGETS_PATH: Path = DEV_DIR / "targets.json"
DB_PATH: Path = DEV_DIR / "resell.db"
TRENDS_OUTPUT_PATH: Path = DEV_DIR / "trends.txt"
LOG_PATH: Path = DEV_DIR / "resell.log"
RUNTIME_DIR: Path = DEV_DIR / ".runtime"
UPDATE_STATE_PATH: Path = DEV_DIR / ".update_state.json"

GITHUB_REPO: str = "https://github.com/scrachies/resellix.git"
GITHUB_BRANCH: str = "main"


@dataclass
class AppConfig:
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    vinted_session_cookie: str = ""
    vinted_access_token_web: str = ""
    vinted_cookie_bundle: str = ""
    vinted_cf_clearance: str = ""
    vinted_datadome: str = ""
    vinted_host: str = "www.vinted.de"
    vinted_locale: str = "de-DE"
    vinted_proxy: str = ""
    serpapi_key: str = ""
    poll_min_seconds: int = 25
    poll_max_seconds: int = 40
    kleinanzeigen_api_url: str = "http://127.0.0.1:8000"
    ebay_host: str = "www.ebay.de"
    sniper_platforms: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def vinted_ready(self) -> bool:
        return bool(self.vinted_host)


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_config() -> AppConfig:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH, override=True)

    cfg = AppConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        vinted_session_cookie=os.getenv("VINTED_SESSION_COOKIE", "").strip(),
        vinted_access_token_web=os.getenv("VINTED_ACCESS_TOKEN_WEB", "").strip(),
        vinted_cookie_bundle=os.getenv("VINTED_COOKIE_BUNDLE", "").strip(),
        vinted_cf_clearance=os.getenv("VINTED_CF_CLEARANCE", "").strip(),
        vinted_datadome=os.getenv("VINTED_DATADOME", "").strip(),
        vinted_host=os.getenv("VINTED_HOST", "www.vinted.de").strip() or "www.vinted.de",
        vinted_locale=os.getenv("VINTED_LOCALE", "de-DE").strip() or "de-DE",
        vinted_proxy=os.getenv("VINTED_PROXY", "").strip() or os.getenv("VINTED_API_HTTPS_PROXY", "").strip(),
        serpapi_key=os.getenv("SERPAPI_KEY", "").strip(),
        poll_min_seconds=_int_env("POLL_MIN_SECONDS", 25),
        poll_max_seconds=_int_env("POLL_MAX_SECONDS", 40),
        kleinanzeigen_api_url=os.getenv("KLEINANZEIGEN_API_URL", "http://127.0.0.1:8000").strip(),
        ebay_host=os.getenv("EBAY_HOST", "www.ebay.de").strip() or "www.ebay.de",
        sniper_platforms=normalize_platforms(os.getenv("SNIPER_PLATFORMS", "vinted,kleinanzeigen,ebay")),
    )
    if cfg.poll_max_seconds < cfg.poll_min_seconds:
        cfg.poll_max_seconds = cfg.poll_min_seconds + 30

    if cfg.vinted_cookie_bundle and not cfg.vinted_session_cookie:
        try:
            from vinted_api import host_to_tld, parse_cookie_string, session_cookie_name

            cookies = parse_cookie_string(cfg.vinted_cookie_bundle)
            tld = host_to_tld(cfg.vinted_host)
            cfg.vinted_session_cookie = (
                cookies.get(session_cookie_name(tld))
                or cookies.get("_vinted_fr_session")
                or ""
            )
        except Exception:
            pass

    return cfg


def ensure_env_file() -> None:
    if ENV_PATH.exists():
        return
    example = DEV_DIR / ".env.example"
    if not example.exists():
        example = APP_DIR / ".env.example"
    if example.exists():
        ENV_PATH.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        ENV_PATH.write_text("", encoding="utf-8")


def save_config(updates: dict[str, Optional[str]]) -> None:
    ensure_env_file()
    for key, value in updates.items():
        value = "" if value is None else str(value)
        set_key(str(ENV_PATH), key, value, quote_mode="never")
