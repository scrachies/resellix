"""SQLite layer: seen listings + match history (for the dashboard feed)."""
from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from config import DB_PATH

_LOCK = threading.Lock()


def _connect(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


_CONN: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        _CONN = _connect()
        init_schema(_CONN)
    return _CONN


def init_schema(conn: sqlite3.Connection) -> None:
    with _LOCK:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS seen_listings (
                listing_id     TEXT PRIMARY KEY,
                first_seen_ts  INTEGER NOT NULL,
                target_label   TEXT
            );

            CREATE TABLE IF NOT EXISTS matches (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id     TEXT NOT NULL,
                target_label   TEXT,
                platform       TEXT DEFAULT 'vinted',
                title          TEXT,
                brand          TEXT,
                size           TEXT,
                status         TEXT,
                price          REAL,
                currency       TEXT,
                expected_price REAL,
                profit         REAL,
                url            TEXT,
                photo_url      TEXT,
                description    TEXT,
                created_ts     INTEGER NOT NULL,
                UNIQUE(listing_id, target_label)
            );

            CREATE TABLE IF NOT EXISTS stats (
                key   TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );
            """
        )
        conn.commit()
        _migrate_matches_columns(conn)


def _migrate_matches_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(matches)").fetchall()}
    if "platform" not in cols:
        conn.execute("ALTER TABLE matches ADD COLUMN platform TEXT DEFAULT 'vinted'")
    if "description" not in cols:
        conn.execute("ALTER TABLE matches ADD COLUMN description TEXT DEFAULT ''")


# ---------------------------------------------------------------------------
# Seen listings
# ---------------------------------------------------------------------------

def is_listing_seen(listing_id: str | int) -> bool:
    conn = get_conn()
    with _LOCK:
        cur = conn.execute(
            "SELECT 1 FROM seen_listings WHERE listing_id = ?",
            (str(listing_id),),
        )
        return cur.fetchone() is not None


def mark_listing_seen(listing_id: str | int, target_label: str = "") -> None:
    conn = get_conn()
    with _LOCK:
        conn.execute(
            "INSERT OR IGNORE INTO seen_listings(listing_id, first_seen_ts, target_label) "
            "VALUES (?,?,?)",
            (str(listing_id), int(time.time()), target_label),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def record_match(match: dict) -> None:
    conn = get_conn()
    with _LOCK:
        conn.execute(
            """
            INSERT OR IGNORE INTO matches
                (listing_id, target_label, platform, title, brand, size, status,
                 price, currency, expected_price, profit, url, photo_url, description, created_ts)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                str(match.get("listing_id")),
                match.get("target_label", ""),
                match.get("platform", "vinted"),
                match.get("title", ""),
                match.get("brand", ""),
                match.get("size", ""),
                match.get("status", ""),
                float(match.get("price") or 0.0),
                match.get("currency", "EUR"),
                float(match.get("expected_price") or 0.0),
                float(match.get("profit") or 0.0),
                match.get("url", ""),
                match.get("photo_url", ""),
                match.get("description", ""),
                int(time.time()),
            ),
        )
        conn.commit()


def recent_matches(limit: int = 100) -> list[dict]:
    conn = get_conn()
    with _LOCK:
        cur = conn.execute(
            "SELECT * FROM matches ORDER BY created_ts DESC LIMIT ?",
            (int(limit),),
        )
        return [dict(row) for row in cur.fetchall()]


def delete_matches_for_target(target_keyword: str) -> int:
    """Remove dashboard feed rows for a deleted snipe target."""
    kw = (target_keyword or "").strip()
    if not kw:
        return 0
    conn = get_conn()
    with _LOCK:
        cur = conn.execute(
            "DELETE FROM matches WHERE target_label = ?",
            (kw,),
        )
        conn.commit()
        return int(cur.rowcount)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def bump_stat(key: str, by: int = 1) -> int:
    conn = get_conn()
    with _LOCK:
        conn.execute(
            "INSERT INTO stats(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value = value + excluded.value",
            (key, by),
        )
        conn.commit()
        cur = conn.execute("SELECT value FROM stats WHERE key = ?", (key,))
        row = cur.fetchone()
        return int(row["value"]) if row else 0


def get_stat(key: str) -> int:
    conn = get_conn()
    with _LOCK:
        cur = conn.execute("SELECT value FROM stats WHERE key = ?", (key,))
        row = cur.fetchone()
        return int(row["value"]) if row else 0


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    conn = get_conn()
    with _LOCK:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
