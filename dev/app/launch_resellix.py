"""One-click launcher: deps, Kleinanzeigen API, then Resellix UI."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from config import APP_DIR, DEV_DIR, ROOT_DIR, RUNTIME_DIR

ROOT = APP_DIR
KA_DIR = ROOT / "vendor" / "ebay-kleinanzeigen-api"
KA_URL = os.getenv("KLEINANZEIGEN_API_URL", "http://127.0.0.1:8000").rstrip("/")
PID_FILE = RUNTIME_DIR / "kleinanzeigen_api.pid"
KA_LOG = DEV_DIR / "kleinanzeigen_api.log"
LEGACY_PLAYWRIGHT_MARKER = RUNTIME_DIR / "playwright_chromium_ok"
KA_REQ = ROOT / "requirements-kleinanzeigen.txt"


def _log(msg: str) -> None:
    print(msg, flush=True)


def _ka_reachable() -> bool:
    try:
        import requests

        r = requests.get(f"{KA_URL}/", timeout=3)
        return r.status_code < 500
    except Exception:
        return False


def _pip_install(args: list[str]) -> bool:
    return subprocess.run(
        [sys.executable, "-m", "pip", *args],
        cwd=str(ROOT),
    ).returncode == 0


def ensure_kleinanzeigen_deps() -> bool:
    if not KA_DIR.is_dir():
        _log("[WARN] vendor/ebay-kleinanzeigen-api missing — Kleinanzeigen disabled.")
        return False
    _log("[Setup] Kleinanzeigen API dependencies…")
    if KA_REQ.is_file():
        _pip_install(["install", "-q", "-r", str(KA_REQ)])
    else:
        _pip_install(
            [
                "install",
                "-q",
                "fastapi",
                "uvicorn",
                "playwright",
                "httpx",
                "aiohttp",
                "loguru",
                "python-multipart",
            ]
        )

    from playwright_setup import (
        CHANNEL_FILE,
        PLAYWRIGHT_MARKER,
        ensure_playwright_browser,
    )

    if LEGACY_PLAYWRIGHT_MARKER.is_file() and not PLAYWRIGHT_MARKER.is_file():
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        PLAYWRIGHT_MARKER.write_text("ok", encoding="utf-8")
        if not CHANNEL_FILE.is_file():
            CHANNEL_FILE.write_text("chromium", encoding="utf-8")

    return ensure_playwright_browser() is not None


def _read_pid() -> int | None:
    try:
        if PID_FILE.is_file():
            return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        pass
    return None


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return str(pid) in (out.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_kleinanzeigen_api() -> None:
    if not KA_DIR.is_dir():
        return
    if _ka_reachable():
        _log("[OK] Kleinanzeigen API already running.")
        return

    pid = _read_pid()
    if pid and _process_alive(pid):
        _log("[Setup] Waiting for Kleinanzeigen API…")
        _wait_ready(90)
        return

    from playwright_setup import apply_playwright_env

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    env = apply_playwright_env()
    env.setdefault("HEADLESS", "true")
    env["PYTHONUNBUFFERED"] = "1"

    log_handle = open(KA_LOG, "a", encoding="utf-8")
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    _log("[Setup] Starting Kleinanzeigen API in background…")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ],
        cwd=str(KA_DIR),
        env=env,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    log_handle.close()
    _wait_ready(180)


def _wait_ready(timeout_sec: int) -> None:
    if _ka_reachable():
        _log("[OK] Kleinanzeigen API ready.")
        return
    _log("[Setup] Waiting for Kleinanzeigen API (browser warmup, please wait)…")
    for i in range(timeout_sec):
        if _ka_reachable():
            _log("[OK] Kleinanzeigen API ready.")
            return
        if i > 0 and i % 15 == 0:
            _log(f"  … still starting ({i}s)")
        time.sleep(1)
    _log(
        "[WARN] Kleinanzeigen API not reachable — Vinted and eBay still work. "
        f"See {KA_LOG.name}"
    )


def run_resellix() -> int:
    import main as resellix_main

    return int(resellix_main.main() or 0)


def main() -> int:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    from config import ensure_env_file, load_config

    try:
        from github_update import check_and_update

        upd = check_and_update(auto_pull=True)
        if upd.message:
            _log(f"[Update] {upd.message}")
    except Exception as exc:
        _log(f"[Update] skipped: {exc}")

    ensure_env_file()

    from pyvinted_client import ensure_pyvinted

    if not ensure_pyvinted():
        _log("[WARN] pyVinted not ready — Vinted search may fail until you restart via start script.")

    cfg = load_config()
    cfg_platforms = ",".join(cfg.sniper_platforms or []).lower()
    try:
        from subscription import get_entitlements

        if "kleinanzeigen" not in get_entitlements().allowed_platforms:
            cfg_platforms = cfg_platforms.replace("kleinanzeigen", "")
    except Exception:
        pass
    if "kleinanzeigen" in cfg_platforms:
        if ensure_kleinanzeigen_deps():
            start_kleinanzeigen_api()
        else:
            _log("[WARN] Skipping Kleinanzeigen API — Playwright not ready.")

    _log("[Start] Opening Resellix…")
    return run_resellix()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)
