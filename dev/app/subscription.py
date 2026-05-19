"""Resellix subscription tiers, signed license keys, and feature gates."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from config import DEV_DIR
from platforms import PLATFORM_EBAY, PLATFORM_KLEINANZEIGEN, PLATFORM_VINTED

log = logging.getLogger("subscription")

LICENSE_PATH = DEV_DIR / "license.key"
MASTER_CODE = "resellix100125"

TIER_FREE = "free"
TIER_PLUS = "plus"
TIER_PRO = "pro"
TIER_MAX = "max"
TIER_UPDATES = "updates"

VALID_TIERS = {TIER_PLUS, TIER_PRO, TIER_MAX, TIER_UPDATES}

TIER_LABELS = {
    TIER_FREE: "Free",
    TIER_PLUS: "Resellix Plus",
    TIER_PRO: "Resellix Pro",
    TIER_MAX: "Resellix Max",
}


@dataclass(frozen=True)
class Entitlements:
    tier: str
    display_name: str
    max_snipe_targets: int
    allowed_platforms: frozenset[str]
    instant_telegram: bool
    poll_min_floor: int
    cheap_deals: bool
    telegram_search: bool
    trends: bool
    beta_features: bool
    git_updates_allowed: bool
    updates_until: Optional[date] = None
    subscription_until: Optional[date] = None
    license_id: str = ""

    @property
    def sidebar_label(self) -> str:
        if self.tier == TIER_FREE:
            return "Plan: Free"
        return f"Plan: {self.display_name}"

    def updates_status_line(self) -> str:
        if self.git_updates_allowed and self.tier == TIER_MAX:
            if self.subscription_until:
                return f"Subscription until {self.subscription_until.isoformat()}"
            return "Max — updates & beta included"
        if self.git_updates_allowed and self.updates_until:
            return f"Free updates until {self.updates_until.isoformat()}"
        if self.updates_until:
            return f"Updates expired ({self.updates_until.isoformat()}) — ask for an Updates license key"
        return "Updates: activate an Updates license key in Settings"


def _license_secret() -> bytes:
    env = os.environ.get("RESELLIX_LICENSE_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    # Set RESELLIX_LICENSE_SECRET in production before generating customer keys.
    seed = "Resellix::ThomasMikhline::license-v1"
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _sign_payload(payload_b64: str) -> str:
    sig = hmac.new(_license_secret(), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(sig[:18])


def generate_license_key(
    tier: str,
    *,
    updates_days: int = 30,
    subscription_days: int = 30,
    license_id: Optional[str] = None,
) -> str:
    """Create a signed key (run scripts/generate_license.py)."""
    tier = tier.strip().lower()
    if tier not in VALID_TIERS:
        raise ValueError(f"Unknown tier: {tier}")

    today = date.today()
    payload: dict[str, Any] = {
        "t": tier,
        "id": license_id or str(uuid.uuid4())[:8],
        "iat": today.isoformat(),
    }
    if tier in (TIER_PLUS, TIER_PRO):
        payload["u"] = (today + timedelta(days=updates_days)).isoformat()
    if tier == TIER_MAX:
        payload["s"] = (today + timedelta(days=subscription_days)).isoformat()
        payload["u"] = payload["s"]
    if tier == TIER_UPDATES:
        payload["u"] = (today + timedelta(days=updates_days)).isoformat()

    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _sign_payload(payload_b64)
    return f"RX-{tier.upper()}-{payload_b64}.{sig}"


def _parse_date(raw: Any) -> Optional[date]:
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _verify_license_key(key: str) -> Optional[dict[str, Any]]:
    key = key.strip()
    if not key.upper().startswith("RX-"):
        return None
    parts = key.split("-", 2)
    if len(parts) < 3:
        return None
    body = parts[2]
    if "." not in body:
        return None
    payload_b64, sig = body.rsplit(".", 1)
    if not hmac.compare_digest(_sign_payload(payload_b64), sig):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (json.JSONDecodeError, ValueError):
        return None
    if payload.get("t") not in VALID_TIERS:
        return None
    return payload


def _load_stored_key() -> str:
    if LICENSE_PATH.is_file():
        return LICENSE_PATH.read_text(encoding="utf-8").strip()
    return ""


def _save_stored_key(key: str) -> None:
    LICENSE_PATH.write_text(key.strip() + "\n", encoding="utf-8")


def _load_activation_meta() -> dict[str, Any]:
    meta_path = DEV_DIR / "license.meta.json"
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_activation_meta(meta: dict[str, Any]) -> None:
    meta_path = DEV_DIR / "license.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def activate_license(code: str) -> tuple[bool, str]:
    """Activate or extend plan from a license key or master code."""
    code = code.strip()
    if not code:
        return False, "Enter a license key."

    if code == MASTER_CODE:
        _save_stored_key(f"RX-MASTER-{_b64url_encode(b'master')}.dev")
        _save_activation_meta(
            {
                "tier": TIER_MAX,
                "master": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return True, "Developer Max license activated."

    payload = _verify_license_key(code)
    if not payload:
        return False, "Invalid or tampered license key."

    tier = str(payload["t"])
    meta = _load_activation_meta()
    today = date.today()

    if tier == TIER_UPDATES:
        current = get_entitlements()
        if current.tier == TIER_FREE:
            return False, "Updates keys extend Plus/Pro/Max — activate a plan first."
        new_until = _parse_date(payload.get("u")) or (today + timedelta(days=30))
        prev = current.updates_until
        if prev and prev > today:
            new_until = max(new_until, prev + timedelta(days=30))
        meta["updates_until"] = new_until.isoformat()
        _save_activation_meta(meta)
        return True, f"Updates extended until {new_until.isoformat()}."

    _save_stored_key(code)
    meta = {
        "tier": tier,
        "master": False,
        "license_id": payload.get("id", ""),
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "updates_until": payload.get("u"),
        "subscription_until": payload.get("s"),
    }
    _save_activation_meta(meta)
    label = TIER_LABELS.get(tier, tier)
    extra = ""
    if u := _parse_date(payload.get("u")):
        extra = f" Updates included until {u.isoformat()}."
    if s := _parse_date(payload.get("s")):
        extra += f" Max subscription until {s.isoformat()}."
    return True, f"{label} activated.{extra}"


def clear_license() -> None:
    for p in (LICENSE_PATH, DEV_DIR / "license.meta.json"):
        if p.is_file():
            p.unlink()


def _entitlements_from_meta(
    tier: str,
    *,
    updates_until: Optional[date],
    subscription_until: Optional[date],
    license_id: str,
    master: bool,
) -> Entitlements:
    today = date.today()

    if master:
        return Entitlements(
            tier=TIER_MAX,
            display_name="Resellix Max (Developer)",
            max_snipe_targets=999,
            allowed_platforms=frozenset({PLATFORM_VINTED, PLATFORM_KLEINANZEIGEN, PLATFORM_EBAY}),
            instant_telegram=True,
            poll_min_floor=8,
            cheap_deals=True,
            telegram_search=True,
            trends=True,
            beta_features=True,
            git_updates_allowed=True,
            updates_until=None,
            subscription_until=None,
            license_id="master",
        )

    updates_ok = bool(updates_until and updates_until >= today)

    if tier == TIER_MAX:
        sub_ok = bool(subscription_until and subscription_until >= today)
        if not sub_ok:
            tier = TIER_FREE
        else:
            return Entitlements(
                tier=TIER_MAX,
                display_name=TIER_LABELS[TIER_MAX],
                max_snipe_targets=999,
                allowed_platforms=frozenset({PLATFORM_VINTED, PLATFORM_KLEINANZEIGEN, PLATFORM_EBAY}),
                instant_telegram=True,
                poll_min_floor=8,
                cheap_deals=True,
                telegram_search=True,
                trends=True,
                beta_features=True,
                git_updates_allowed=True,
                updates_until=subscription_until,
                subscription_until=subscription_until,
                license_id=license_id,
            )

    if tier == TIER_PRO:
        return Entitlements(
            tier=TIER_PRO,
            display_name=TIER_LABELS[TIER_PRO],
            max_snipe_targets=5,
            allowed_platforms=frozenset({PLATFORM_VINTED, PLATFORM_KLEINANZEIGEN, PLATFORM_EBAY}),
            instant_telegram=True,
            poll_min_floor=8,
            cheap_deals=True,
            telegram_search=True,
            trends=True,
            beta_features=False,
            git_updates_allowed=updates_ok,
            updates_until=updates_until,
            license_id=license_id,
        )

    if tier == TIER_PLUS:
        return Entitlements(
            tier=TIER_PLUS,
            display_name=TIER_LABELS[TIER_PLUS],
            max_snipe_targets=2,
            allowed_platforms=frozenset({PLATFORM_VINTED}),
            instant_telegram=False,
            poll_min_floor=45,
            cheap_deals=False,
            telegram_search=False,
            trends=False,
            beta_features=False,
            git_updates_allowed=updates_ok,
            updates_until=updates_until,
            license_id=license_id,
        )

    return Entitlements(
        tier=TIER_FREE,
        display_name=TIER_LABELS[TIER_FREE],
        max_snipe_targets=1,
        allowed_platforms=frozenset({PLATFORM_VINTED}),
        instant_telegram=False,
        poll_min_floor=50,
        cheap_deals=False,
        telegram_search=False,
        trends=False,
        beta_features=False,
        git_updates_allowed=False,
        license_id="",
    )


def get_entitlements() -> Entitlements:
    meta = _load_activation_meta()
    if meta.get("master"):
        return _entitlements_from_meta(TIER_MAX, updates_until=None, subscription_until=None, license_id="master", master=True)

    key = _load_stored_key()
    if not key:
        return _entitlements_from_meta(TIER_FREE, updates_until=None, subscription_until=None, license_id="", master=False)

    payload = _verify_license_key(key)
    if not payload:
        log.warning("Stored license invalid — using Free tier")
        return _entitlements_from_meta(TIER_FREE, updates_until=None, subscription_until=None, license_id="", master=False)

    tier = str(payload["t"])
    meta_updates = _parse_date(meta.get("updates_until"))
    payload_updates = _parse_date(payload.get("u"))
    updates_until = meta_updates
    if payload_updates:
        if not updates_until or payload_updates > updates_until:
            updates_until = payload_updates

    return _entitlements_from_meta(
        tier,
        updates_until=updates_until,
        subscription_until=_parse_date(payload.get("s")),
        license_id=str(payload.get("id", "")),
        master=False,
    )


def can_add_snipe_target(current_count: int) -> tuple[bool, str]:
    ent = get_entitlements()
    if current_count >= ent.max_snipe_targets:
        return False, (
            f"{ent.display_name} allows max {ent.max_snipe_targets} snipe target(s). "
            "Upgrade your license in Settings."
        )
    return True, ""


def filter_platforms(platforms: list[str]) -> list[str]:
    ent = get_entitlements()
    allowed = ent.allowed_platforms
    return [p for p in platforms if p in allowed]


def clamp_poll_intervals(poll_min: int, poll_max: int) -> tuple[int, int]:
    ent = get_entitlements()
    lo = max(poll_min, ent.poll_min_floor)
    hi = max(poll_max, lo + 5)
    return lo, hi


def require_feature(feature: str) -> tuple[bool, str]:
    ent = get_entitlements()
    checks = {
        "cheap_deals": (ent.cheap_deals, "Cheap Deals requires Resellix Pro or Max."),
        "telegram_search": (ent.telegram_search, "Telegram search requires Resellix Pro or Max."),
        "trends": (ent.trends, "Steal Niches requires Resellix Pro or Max."),
        "kleinanzeigen": (
            PLATFORM_KLEINANZEIGEN in ent.allowed_platforms,
            "Kleinanzeigen requires Resellix Pro or Max.",
        ),
        "ebay": (
            PLATFORM_EBAY in ent.allowed_platforms,
            "eBay requires Resellix Pro or Max.",
        ),
        "instant_alerts": (
            ent.instant_telegram,
            "Faster Telegram alerts require Resellix Pro or Max (Plus uses slower polling).",
        ),
        "beta": (ent.beta_features, "Beta features require Resellix Max."),
    }
    ok, msg = checks.get(feature, (True, ""))
    return ok, msg


def git_updates_blocked_message() -> str:
    ent = get_entitlements()
    if ent.git_updates_allowed:
        return ""
    return (
        "Git updates not included on your plan right now. "
        "Plus/Pro include 1 month of updates; extend with an Updates license key "
        "or upgrade to Resellix Max."
    )
