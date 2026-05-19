"""Adapter for herissondev/vinted-api-wrapper (pyVinted).

Uses the bundled copy in ``dev/app/vendor/pyVinted`` (shipped with Resellix).
There is no reliable ``pip install pyvinted`` package on PyPI.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

from config import APP_DIR, AppConfig

log = logging.getLogger("pyvinted")

_VENDOR = APP_DIR / "vendor"
_BUNDLE = _VENDOR / "pyVinted"
_PYVINTED: Any = None


def _ensure_pyvinted_path() -> None:
    vendor_str = str(_VENDOR)
    if _VENDOR.is_dir() and vendor_str not in sys.path:
        sys.path.insert(0, vendor_str)


def _import_pyvinted():
    if not _BUNDLE.is_dir():
        raise RuntimeError(
            f"Bundled pyVinted missing ({_BUNDLE}). "
            "Re-clone the repo or restore dev/app/vendor/pyVinted."
        )
    _ensure_pyvinted_path()
    try:
        from pyVinted import Vinted
        from pyVinted.requester import requester

        return Vinted, requester
    except ImportError as exc:
        raise RuntimeError(
            "pyVinted could not be loaded from dev/app/vendor/pyVinted. "
            "Run windows\\startwindows.bat or apple/startapple.command again."
        ) from exc


def ensure_pyvinted() -> bool:
    """Verify bundled pyVinted imports (no pip install)."""
    try:
        _import_pyvinted()
        return True
    except RuntimeError as exc:
        log.error("%s", exc)
        return False


def _proxy_dict(proxy_url: str) -> Optional[dict[str, str]]:
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}


def prepare_session(cfg: AppConfig, catalog_url: str) -> None:
    if not ensure_pyvinted():
        raise RuntimeError(
            "pyVinted is not available. Restore dev/app/vendor/pyVinted and restart."
        )
    _, requester = _import_pyvinted()

    netloc = urlparse(catalog_url).netloc or cfg.vinted_host or "www.vinted.de"

    requester.setLocale(netloc)

    if cfg.vinted_session_cookie:
        tld = netloc.split(".")[-1] if "." in netloc else "de"
        for name in (f"_vinted_{tld}_session", "_vinted_fr_session", "_vinted_de_session"):
            try:
                requester.session.cookies.set(name, cfg.vinted_session_cookie, domain=netloc)
            except Exception:
                pass

    requester.setCookies()


def get_vinted(cfg: AppConfig) -> Any:
    global _PYVINTED
    Vinted, requester = _import_pyvinted()
    proxy = _proxy_dict(cfg.vinted_proxy)
    if proxy:
        requester.session.proxies.update(proxy)
    if _PYVINTED is None:
        _PYVINTED = Vinted(proxy=proxy)
    return _PYVINTED


def reset_client() -> None:
    global _PYVINTED
    _PYVINTED = None


def search_catalog_url(
    cfg: AppConfig,
    catalog_url: str,
    per_page: int = 20,
    page: int = 1,
) -> list[Any]:
    prepare_session(cfg, catalog_url)
    vinted = get_vinted(cfg)
    items = vinted.items.search(catalog_url, nbrItems=per_page, page=page)
    log.info("pyVinted: %s items from %s", len(items), catalog_url[:80])
    return items


def diagnose(cfg: AppConfig) -> list[str]:
    from vinted_api import build_catalog_url

    lines = [
        "Backend: pyVinted (bundled dev/app/vendor/pyVinted)",
        f"Host: {cfg.vinted_host}",
        f"Bundle: {_BUNDLE} ({'found' if _BUNDLE.is_dir() else 'MISSING'})",
        "",
    ]
    if not ensure_pyvinted():
        lines.append("Import: FAILED – restore vendor/pyVinted from the Resellix repo.")
        return lines

    lines.append("Import: OK")
    test_url = build_catalog_url(
        cfg.vinted_host, search_text="nike", max_price=50, per_page=3, page=1
    )
    lines.append(f"Test URL: {test_url}")
    try:
        items = search_catalog_url(cfg, test_url, per_page=3, page=1)
        lines.append(f"Search: OK – {len(items)} item(s)")
        if items:
            lines.append(f"  e.g. {items[0].title} – {items[0].price} {items[0].currency}")
    except Exception as exc:
        lines.append(f"Search: FAILED – {exc}")
    return lines
