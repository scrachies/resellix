"""Python port of Androz2091/vinted-api (npm).

Same flow as:
  const vinted = require('vinted-api');
  vinted.search('https://www.vinted.fr/vetements?brand_id[]=53')

1) GET https://www.vinted.{tld}/  → extract _vinted_{tld}_session
2) GET https://www.vinted.{tld}/api/v2/catalog/items?{query from URL}
"""
from __future__ import annotations

import logging
import os
import re
import threading
from typing import Any, Optional
from urllib.parse import quote_plus, unquote

import requests

try:
    from fake_useragent import UserAgent
    _UA = UserAgent()
except Exception:
    _UA = None

log = logging.getLogger("vinted_api")

# Per-TLD session cache (like the JS Map)
_COOKIE_CACHE: dict[str, str] = {}
_CACHE_LOCK = threading.Lock()

_MISSING_ID_PARAMS = ("catalog", "status")
_URL_TLD_RE = re.compile(r"^https://www\.vinted\.([a-z]+)", re.IGNORECASE)
_PARAM_RE = re.compile(
    r"(?:([a-z_]+)(\[\])?=([a-zA-Z 0-9._À-ú+%]+)&?)",
    re.IGNORECASE,
)

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _user_agent() -> str:
    if _UA is not None:
        try:
            return _UA.random
        except Exception:
            pass
    return _DEFAULT_UA


def host_to_tld(host: str) -> str:
    """www.vinted.de → de"""
    host = (host or "www.vinted.de").lower().strip()
    if host.startswith("www.vinted."):
        return host.split(".", 2)[-1]
    if host.startswith("vinted."):
        return host.split(".", 1)[-1]
    return "de"


def session_cookie_name(tld: str) -> str:
    return f"_vinted_{tld.lower()}_session"


def env_cookie_for_tld(tld: str) -> str:
    key = f"VINTED_API_{tld.upper()}_COOKIE"
    return os.getenv(key, "").strip()


def parse_vinted_url(
    url: str,
    custom_params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Port of parseVintedURL() from vinted-api."""
    try:
        decoded = unquote(url)
        m = _URL_TLD_RE.match(decoded)
        if not m:
            return {"valid_url": False}

        tld = m.group(1).lower()
        mapped: dict[str, Any] = {}

        for param_name, is_array, param_value in _PARAM_RE.findall(decoded):
            if param_value and " " in param_value:
                param_value = param_value.replace(" ", "+")
            if is_array:
                if param_name in _MISSING_ID_PARAMS:
                    param_name = f"{param_name}_id"
                key = f"{param_name}s"
                mapped.setdefault(key, [])
                mapped[key].append(param_value)
            else:
                mapped[param_name] = param_value

        if custom_params:
            mapped.update(custom_params)

        final: list[str] = []
        for key, value in mapped.items():
            if isinstance(value, list):
                final.append(f"{key}={','.join(str(v) for v in value)}")
            else:
                final.append(f"{key}={value}")

        return {
            "valid_url": True,
            "tld": tld,
            "domain": tld,
            "querystring": "&".join(final),
        }
    except Exception as exc:
        log.debug("parse_vinted_url failed: %s", exc)
        return {"valid_url": False}


def fetch_cookie(
    tld: str,
    session: Optional[requests.Session] = None,
    proxy: Optional[str] = None,
) -> str:
    """Port of fetchCookie() – loads _vinted_{tld}_session from the storefront."""
    tld = tld.lower()
    sess = session or requests.Session()
    headers = {"User-Agent": _user_agent()}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    cname = session_cookie_name(tld)

    for base in (f"https://www.vinted.{tld}", f"https://vinted.{tld}"):
        try:
            resp = sess.get(
                f"{base}/",
                headers=headers,
                timeout=25,
                allow_redirects=True,
                proxies=proxies,
            )
        except requests.RequestException as exc:
            log.warning("fetch_cookie %s: %s", base, exc)
            continue

        if cname in resp.cookies:
            token = resp.cookies.get(cname) or ""
            if token:
                with _CACHE_LOCK:
                    _COOKIE_CACHE[tld] = token
                log.info("Fetched %s from %s", cname, base)
                return token

        # Fallback: parse Set-Cookie header text
        raw = resp.headers.get("Set-Cookie", "") or ""
        marker = f"{cname}="
        if marker in raw:
            token = raw.split(marker, 1)[1].split(";", 1)[0].strip()
            if token:
                with _CACHE_LOCK:
                    _COOKIE_CACHE[tld] = token
                return token

    return ""


def get_session_token(
    tld: str,
    manual: str = "",
    session: Optional[requests.Session] = None,
    proxy: Optional[str] = None,
) -> str:
    """Cached → env → manual → fetch."""
    tld = tld.lower()
    if manual:
        return manual

    with _CACHE_LOCK:
        cached = _COOKIE_CACHE.get(tld, "")

    if cached:
        return cached

    env = env_cookie_for_tld(tld)
    if env:
        with _CACHE_LOCK:
            _COOKIE_CACHE[tld] = env
        return env

    return fetch_cookie(tld, session=session, proxy=proxy)


def search_catalog_url(
    catalog_url: str,
    *,
    manual_cookie: str = "",
    proxy: Optional[str] = None,
    extra_params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Port of search() – pass a full Vinted catalog URL like the npm package.

    Returns the raw JSON (with ``items`` list).
    """
    parsed = parse_vinted_url(catalog_url, custom_params=extra_params)
    if not parsed.get("valid_url"):
        log.warning("Invalid Vinted URL: %s", catalog_url)
        return {"items": []}

    tld: str = parsed["tld"]
    qs: str = parsed["querystring"]

    sess = requests.Session()
    token = get_session_token(tld, manual=manual_cookie, session=sess, proxy=proxy)
    if not token:
        raise VintedApiError(
            f"Could not obtain {session_cookie_name(tld)}. "
            f"Open https://www.vinted.{tld} in a browser or set VINTED_SESSION_COOKIE in .env"
        )

    api = f"https://www.vinted.{tld}/api/v2/catalog/items?{qs}"
    cname = session_cookie_name(tld)
    headers = {
        "Cookie": f"{cname}={token}",
        "User-Agent": _user_agent(),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9",
    }
    proxies = {"http": proxy, "https": proxy} if proxy else None

    try:
        resp = sess.get(api, headers=headers, timeout=25, proxies=proxies)
    except requests.RequestException as exc:
        raise VintedApiError(f"Network error: {exc}") from exc

    if resp.status_code in (401, 403):
        # Retry once with fresh cookie (like the JS lib)
        with _CACHE_LOCK:
            _COOKIE_CACHE.pop(tld, None)
        token = fetch_cookie(tld, session=sess, proxy=proxy)
        if token:
            headers["Cookie"] = f"{cname}={token}"
            resp = sess.get(api, headers=headers, timeout=25, proxies=proxies)

    if resp.status_code == 429:
        raise VintedApiRateLimit("Vinted rate-limited (429)")

    if resp.status_code != 200:
        raise VintedApiError(f"HTTP {resp.status_code}: {resp.text[:300]}")

    try:
        return resp.json()
    except ValueError as exc:
        raise VintedApiError(f"Invalid JSON: {resp.text[:200]}") from exc


def build_catalog_url(
    host: str,
    *,
    search_text: str = "",
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    order: str = "newest_first",
    brand_id: Optional[int] = None,
    catalog_id: Optional[int] = None,
    per_page: int = 20,
    page: int = 1,
) -> str:
    """Build a catalog URL that parse_vinted_url understands."""
    tld = host_to_tld(host)
    host = f"www.vinted.{tld}"
    parts = [f"https://{host}/catalog?"]
    q: list[str] = []
    if search_text:
        q.append(f"search_text={quote_plus(search_text)}")
    if min_price is not None and min_price > 0:
        q.append(f"price_from={min_price:.2f}")
    if max_price is not None:
        q.append(f"price_to={max_price:.2f}")
    if order:
        q.append(f"order={quote_plus(order)}")
    if brand_id is not None:
        q.append(f"brand_ids[]={brand_id}")
    if catalog_id is not None:
        q.append(f"catalog_ids[]={catalog_id}")
    q.append(f"per_page={per_page}")
    q.append(f"page={page}")
    return parts[0] + "&".join(q)


class VintedApiError(RuntimeError):
    pass


class VintedApiRateLimit(VintedApiError):
    pass


def parse_cookie_string(raw: str) -> dict[str, str]:
    """Parse ``name=value; name2=value2`` from DevTools."""
    out: dict[str, str] = {}
    if not raw or not raw.strip():
        return out
    text = raw.strip()
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
