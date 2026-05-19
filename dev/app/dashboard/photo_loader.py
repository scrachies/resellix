"""Async photo loader: fetches URLs in worker threads, emits QPixmap on the UI thread."""
from __future__ import annotations

import logging
import threading
from collections import OrderedDict

import requests
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap

log = logging.getLogger("dashboard.photo_loader")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Limit parallel image downloads (refreshing the feed can spawn many cards at once).
_FETCH_SEM = threading.Semaphore(6)

# URL → QPixmap (avoid re-downloading when user refreshes the feed).
_CACHE: OrderedDict[str, QPixmap] = OrderedDict()
_MAX_CACHE = 128


def _cache_get(url: str) -> QPixmap | None:
    pm = _CACHE.get(url)
    if pm is not None:
        _CACHE.move_to_end(url)
    return pm


def _cache_put(url: str, pm: QPixmap) -> None:
    _CACHE[url] = pm
    _CACHE.move_to_end(url)
    while len(_CACHE) > _MAX_CACHE:
        _CACHE.popitem(last=False)


def _qt_object_alive(obj: QObject) -> bool:
    try:
        from shiboken6 import isValid

        return isValid(obj)
    except Exception:
        return True


class PhotoLoader(QObject):
    """Single-shot photo loader. One instance per DealCard; call cancel() before destroy."""

    loaded = pyqtSignal(QPixmap)
    failed = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cancelled = False
        self._url = ""

    def cancel(self) -> None:
        self._cancelled = True

    def fetch(self, url: str, max_bytes: int = 4_000_000) -> None:
        if self._cancelled:
            return
        if not url:
            self._emit_failed("no url")
            return

        self._url = url
        cached = _cache_get(url)
        if cached is not None and not cached.isNull():
            self._emit_loaded(cached)
            return

        t = threading.Thread(
            target=self._do_fetch,
            args=(url, max_bytes),
            daemon=True,
            name="PhotoLoader",
        )
        t.start()

    def _emit_loaded(self, pm: QPixmap) -> None:
        if self._cancelled or not _qt_object_alive(self):
            return
        try:
            self.loaded.emit(pm)
        except RuntimeError:
            pass

    def _emit_failed(self, msg: str) -> None:
        if self._cancelled or not _qt_object_alive(self):
            return
        try:
            self.failed.emit(msg)
        except RuntimeError:
            pass

    def _do_fetch(self, url: str, max_bytes: int) -> None:
        if self._cancelled:
            return
        with _FETCH_SEM:
            if self._cancelled:
                return
            try:
                resp = requests.get(
                    url,
                    headers={
                        "User-Agent": _UA,
                        "Accept": "image/*,*/*;q=0.8",
                        "Referer": "https://www.vinted.de/",
                    },
                    timeout=(6, 14),
                    stream=True,
                )
                resp.raise_for_status()
                data = bytearray()
                for chunk in resp.iter_content(chunk_size=16384):
                    if self._cancelled:
                        return
                    if not chunk:
                        continue
                    data.extend(chunk)
                    if len(data) > max_bytes:
                        break
            except requests.exceptions.Timeout:
                self._emit_failed("timeout")
                return
            except requests.exceptions.RequestException as exc:
                self._emit_failed(str(exc)[:120])
                return
            except Exception as exc:
                log.debug("photo fetch error: %s", exc)
                self._emit_failed("fetch failed")
                return

        if self._cancelled or not _qt_object_alive(self):
            return

        pm = QPixmap()
        if pm.loadFromData(bytes(data)):
            _cache_put(url, pm)
            self._emit_loaded(pm)
        else:
            self._emit_failed("could not decode image")
