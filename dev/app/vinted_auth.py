"""Vinted authentication helpers (2025–2026).

Vinted no longer accepts only `_vinted_fr_session` on API calls. Community workarounds:

1. **OAuth guest token** – POST /oauth/token (client_id=ios) → Bearer header (vlourme/vintedpy).
2. **access_token_web** – Set on homepage visit; often required *with* session cookie.
3. **Cloudflare** – cf_clearance / datadome cookies when your IP is challenged.
4. **vinted-scraper** – pip package that bootstraps cookies (optional).

See README “Vinted access” for copy-paste steps from Chrome.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

from config import AppConfig

log = logging.getLogger("vinted.auth")

# iOS app fingerprint (used by working open-source clients)
IOS_UA = (
    "vinted-ios Vinted/24.34.0 (lt.manodrabuziai.fr; build:30123; iOS 17.0.0) iPhone14,2"
)
IOS_APP_VERSION = "24.34.0"
IOS_DEVICE = "iPhone14,2"

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class AuthState:
    mode: str = "none"  # oauth | cookies | library | none
    bearer_token: str = ""
    token_expires_at: float = 0.0
    refresh_token: str = ""
    cookies: dict[str, str] = field(default_factory=dict)
    last_error: str = ""

    @property
    def ready(self) -> bool:
        if self.mode == "oauth" and self.bearer_token:
            if self.token_expires_at <= 0 or time.time() < self.token_expires_at - 30:
                return True
        if self.mode == "cookies" and self.cookies:
            return True
        if self.mode == "library":
            try:
                import vinted_scraper  # noqa: F401
                return True
            except ImportError:
                return False
        return False


def parse_cookie_string(raw: str) -> dict[str, str]:
    """Parse 'name=value; name2=value2' or DevTools copy format."""
    out: dict[str, str] = {}
    if not raw or not raw.strip():
        return out
    text = raw.strip()
    # DevTools sometimes copies as multiple lines "name\tvalue"
    if "\n" in text and "=" not in text.split("\n", 1)[0]:
        for line in text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                out[parts[0].strip()] = parts[1].strip()
        if out:
            return out
    for part in re.split(r"[;\n]", text):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name, value = name.strip(), value.strip()
        if name:
            out[name] = value
    return out


def merge_config_cookies(cfg: AppConfig) -> dict[str, str]:
    cookies = parse_cookie_string(cfg.vinted_cookie_bundle)
    if cfg.vinted_session_cookie:
        cookies.setdefault("_vinted_fr_session", cfg.vinted_session_cookie)
    if cfg.vinted_access_token_web:
        cookies.setdefault("access_token_web", cfg.vinted_access_token_web)
    if cfg.vinted_cf_clearance:
        cookies.setdefault("cf_clearance", cfg.vinted_cf_clearance)
    if cfg.vinted_datadome:
        cookies.setdefault("datadome", cfg.vinted_datadome)
    return cookies


def _base_url(cfg: AppConfig) -> str:
    return f"https://{cfg.vinted_host}"


def fetch_oauth_token(cfg: AppConfig, state: AuthState) -> bool:
    """Anonymous iOS OAuth token (no Vinted login). Works on many regions."""
    url = f"{_base_url(cfg)}/oauth/token"
    payload: dict[str, Any] = {
        "grant_type": "password",
        "client_id": "ios",
        "scope": "public",
    }
    if state.refresh_token:
        payload = {
            "grant_type": "refresh_token",
            "client_id": "ios",
            "refresh_token": state.refresh_token,
        }
    try:
        resp = requests.post(
            url,
            json=payload,
            headers={"User-Agent": IOS_UA, "Accept": "application/json"},
            timeout=20,
        )
    except requests.RequestException as exc:
        state.last_error = f"OAuth network error: {exc}"
        return False

    if resp.status_code != 200:
        state.last_error = f"OAuth HTTP {resp.status_code}: {resp.text[:300]}"
        log.warning("OAuth failed: %s", state.last_error)
        return False

    try:
        data = resp.json()
    except ValueError:
        state.last_error = "OAuth returned non-JSON"
        return False

    token = data.get("access_token") or ""
    if not token:
        state.last_error = "OAuth response missing access_token"
        return False

    state.bearer_token = token
    state.refresh_token = data.get("refresh_token") or state.refresh_token
    created = float(data.get("created_at") or time.time())
    expires_in = float(data.get("expires_in") or 3600)
    state.token_expires_at = created + expires_in
    state.mode = "oauth"
    state.last_error = ""
    log.info("Vinted OAuth token acquired (expires in %.0fs)", expires_in)
    return True


def bootstrap_web_cookies(cfg: AppConfig, session: requests.Session) -> dict[str, str]:
    """Visit homepage like a browser to obtain access_token_web (+ friends)."""
    url = f"{_base_url(cfg)}/"
    headers = {
        "User-Agent": CHROME_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": cfg.vinted_locale,
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        resp = session.get(url, headers=headers, timeout=25, allow_redirects=True)
    except requests.RequestException as exc:
        log.warning("Cookie bootstrap network error: %s", exc)
        return {}

    if resp.status_code == 403:
        log.warning(
            "Homepage returned 403 (Cloudflare/Datadome). "
            "Paste cf_clearance + access_token_web from browser in Settings."
        )
        return {}

    found = {c.name: c.value for c in session.cookies}
    # Important names per GitHub vinted_scraper discussions
    for key in ("access_token_web", "_vinted_fr_session", "refresh_token_web", "datadome", "cf_clearance"):
        if key in found:
            log.info("Bootstrapped cookie: %s", key)
    return found


def try_cloudscraper_bootstrap(cfg: AppConfig) -> dict[str, str]:
    try:
        import cloudscraper  # type: ignore
    except ImportError:
        return {}
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    url = f"{_base_url(cfg)}/"
    try:
        resp = scraper.get(url, timeout=25)
        if resp.status_code != 200:
            return {}
        return {c.name: c.value for c in scraper.cookies}
    except Exception as exc:
        log.warning("cloudscraper bootstrap failed: %s", exc)
        return {}


def try_vinted_scraper_library(cfg: AppConfig) -> list[dict]:
    """Optional: vinted-scraper package (pip install vinted-scraper)."""
    try:
        from vinted_scraper import VintedScraper  # type: ignore
    except ImportError:
        return []
    base = _base_url(cfg)
    try:
        scraper = VintedScraper(base)
        items = scraper.search({"search_text": "nike", "per_page": 3})
    except Exception as exc:
        log.warning("vinted-scraper library failed: %s", exc)
        return []
    out: list[dict] = []
    for item in items[:3]:
        out.append(
            {
                "id": getattr(item, "id", None),
                "title": getattr(item, "title", ""),
                "price": getattr(item, "price", 0),
            }
        )
    return out


class VintedAuthManager:
    """Resolves auth once, refreshes OAuth when needed."""

    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.state = AuthState()
        self._session = requests.Session()

    def refresh_config(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.state = AuthState()
        self._session.cookies.clear()

    def ensure_auth(self, force: bool = False) -> AuthState:
        if not force and self.state.ready:
            if self.state.mode == "oauth" and time.time() >= self.state.token_expires_at - 30:
                fetch_oauth_token(self.cfg, self.state)
            if self.state.ready:
                return self.state

        mode = (self.cfg.vinted_auth_mode or "auto").lower().strip()

        if mode in ("auto", "oauth"):
            if fetch_oauth_token(self.cfg, self.state):
                return self.state

        if mode in ("auto", "cookies"):
            manual = merge_config_cookies(self.cfg)
            if manual:
                self.state.cookies = manual
                self.state.mode = "cookies"
                self.state.last_error = ""
                return self.state

            self._session.cookies.clear()
            boot = bootstrap_web_cookies(self.cfg, self._session)
            if not boot:
                boot = try_cloudscraper_bootstrap(self.cfg)
            if boot:
                self.state.cookies = boot
                self.state.mode = "cookies"
                self.state.last_error = ""
                return self.state

        if mode == "library":
            try:
                import vinted_scraper  # noqa: F401
                self.state.mode = "library"
                self.state.last_error = ""
                return self.state
            except ImportError:
                self.state.last_error = "pip install vinted-scraper for library mode"

        if mode == "auto":
            try:
                import vinted_scraper  # noqa: F401
                self.state.mode = "library"
                self.state.last_error = ""
                log.info("Falling back to vinted-scraper library for searches")
                return self.state
            except ImportError:
                pass

        if not self.state.last_error:
            self.state.last_error = (
                "All auth methods failed. Paste cookies from Chrome (access_token_web + "
                "_vinted_fr_session + cf_clearance) or install: pip install cloudscraper vinted-scraper"
            )
        return self.state

    def apply_to_session(self, session: requests.Session, for_api: bool = True) -> None:
        """Attach headers/cookies to a requests.Session."""
        st = self.ensure_auth()
        host = self.cfg.vinted_host

        if st.mode == "oauth" and st.bearer_token:
            session.headers.update(
                {
                    "Authorization": f"Bearer {st.bearer_token}",
                    "User-Agent": IOS_UA,
                    "x-app-version": IOS_APP_VERSION,
                    "x-device-model": IOS_DEVICE,
                    "short-bundle-version": IOS_APP_VERSION,
                    "Accept": "application/json",
                    "Accept-Language": self.cfg.vinted_locale,
                }
            )
            return

        if st.mode == "cookies" and st.cookies:
            session.headers.update(
                {
                    "User-Agent": CHROME_UA,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": self.cfg.vinted_locale,
                    "Referer": f"https://{host}/",
                    "Origin": f"https://{host}",
                    "X-Requested-With": "XMLHttpRequest",
                }
            )
            session.cookies.clear()
            for name, value in st.cookies.items():
                session.cookies.set(name, value, domain=host)
            return

        # fallback chrome headers (may still 401)
        session.headers.update(
            {
                "User-Agent": CHROME_UA,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": self.cfg.vinted_locale,
                "Referer": f"https://{host}/",
                "Origin": f"https://{host}",
            }
        )


def diagnose(cfg: AppConfig) -> list[str]:
    """Run all methods and return human-readable lines for the UI."""
    lines: list[str] = []
    mgr = VintedAuthManager(cfg)

    lines.append(f"Host: {cfg.vinted_host}")
    lines.append(f"Auth mode setting: {cfg.vinted_auth_mode or 'auto'}")
    lines.append("")

    lines.append("1) OAuth guest token (iOS client)…")
    st = AuthState()
    if fetch_oauth_token(cfg, st):
        lines.append("   OK – got Bearer access_token")
        # probe search
        sess = requests.Session()
        mgr.state = st
        mgr.apply_to_session(sess)
        try:
            r = sess.get(
                f"https://{cfg.vinted_host}/api/v2/catalog/items",
                params={"search_text": "nike", "per_page": 1, "page": 1},
                timeout=20,
            )
            lines.append(f"   Search probe: HTTP {r.status_code}")
            if r.status_code == 200:
                n = len(r.json().get("items", []))
                lines.append(f"   => {n} item(s) returned – use auth mode 'oauth' or 'auto'")
        except Exception as exc:
            lines.append(f"   Search probe error: {exc}")
    else:
        lines.append(f"   FAILED – {st.last_error}")

    lines.append("")
    lines.append("2) Homepage cookie bootstrap…")
    sess = requests.Session()
    boot = bootstrap_web_cookies(cfg, sess)
    if boot:
        lines.append(f"   OK – cookies: {', '.join(boot.keys())}")
    else:
        lines.append("   FAILED – no cookies (often Cloudflare 403 on your IP)")

    lines.append("")
    lines.append("3) cloudscraper bootstrap…")
    cs = try_cloudscraper_bootstrap(cfg)
    if cs:
        lines.append(f"   OK – cookies: {', '.join(cs.keys())}")
    else:
        lines.append("   skipped or failed (pip install cloudscraper)")

    manual = merge_config_cookies(cfg)
    lines.append("")
    lines.append(f"4) Manual cookies from settings: {len(manual)} name(s)")
    if manual:
        lines.append(f"   {', '.join(manual.keys())}")

    lines.append("")
    lines.append("5) vinted-scraper library…")
    try:
        from vinted_scraper import VintedScraper  # noqa: F401
        lines.append("   package installed – try auth mode 'library'")
    except ImportError:
        lines.append("   not installed (pip install vinted-scraper)")

    lines.append("")
    lines.append("Tip: In Chrome DevTools → Application → Cookies, copy ALL of:")
    lines.append("  access_token_web, _vinted_fr_session, cf_clearance, datadome")
    lines.append("Paste as one line into 'Cookie bundle' in Settings.")
    return lines
