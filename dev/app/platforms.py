"""Marketplace identifiers for sniper + dashboard."""
from __future__ import annotations

PLATFORM_VINTED = "vinted"
PLATFORM_KLEINANZEIGEN = "kleinanzeigen"
PLATFORM_EBAY = "ebay"

ALL_PLATFORMS: list[str] = [
    PLATFORM_VINTED,
    PLATFORM_KLEINANZEIGEN,
    PLATFORM_EBAY,
]

PLATFORM_LABELS: dict[str, str] = {
    PLATFORM_VINTED: "Vinted",
    PLATFORM_KLEINANZEIGEN: "Kleinanzeigen",
    PLATFORM_EBAY: "eBay",
}


def normalize_platforms(raw: object, default: list[str] | None = None) -> list[str]:
    if raw is None:
        return list(default or [PLATFORM_VINTED])
    if isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.replace(";", ",").split(",") if p.strip()]
    elif isinstance(raw, list):
        parts = [str(p).strip().lower() for p in raw if str(p).strip()]
    else:
        return list(default or [PLATFORM_VINTED])
    if not parts or "all" in parts:
        return list(ALL_PLATFORMS)
    out: list[str] = []
    for p in parts:
        if p in ALL_PLATFORMS and p not in out:
            out.append(p)
    return out or list(default or [PLATFORM_VINTED])


def composite_listing_id(platform: str, raw_id: str) -> str:
    rid = str(raw_id or "").strip()
    if not rid:
        return ""
    prefix = f"{platform}:"
    if rid.startswith(prefix):
        return rid
    return f"{prefix}{rid}"


def platform_label(platform: str) -> str:
    return PLATFORM_LABELS.get(platform or "", platform or "—")
