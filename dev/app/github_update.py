"""Check GitHub for Resellix updates and pull when behind origin."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config import APP_DIR, DEV_DIR, GITHUB_BRANCH, GITHUB_REPO, ROOT_DIR, UPDATE_STATE_PATH

log = logging.getLogger("update")


@dataclass
class UpdateResult:
    checked: bool
    update_available: bool
    pulled: bool
    message: str
    local_sha: str = ""
    remote_sha: str = ""


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _git_ok() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=10, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _read_state() -> dict:
    if not UPDATE_STATE_PATH.is_file():
        return {}
    try:
        return json.loads(UPDATE_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_state(**fields: object) -> None:
    data = _read_state()
    data.update(fields)
    data["last_check_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        UPDATE_STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        log.debug("could not write update state: %s", exc)


def ensure_git_repo() -> bool:
    """Init git + remote if folder was copied without .git."""
    if (ROOT_DIR / ".git").is_dir():
        return True
    if not _git_ok():
        return False
    try:
        _run_git(["init"], ROOT_DIR)
        _run_git(["remote", "add", "origin", GITHUB_REPO], ROOT_DIR)
        _run_git(["fetch", "origin", GITHUB_BRANCH], ROOT_DIR)
        _run_git(["checkout", "-B", GITHUB_BRANCH, f"origin/{GITHUB_BRANCH}"], ROOT_DIR)
        return True
    except Exception as exc:
        log.warning("git init failed: %s", exc)
        return False


def check_and_update(*, auto_pull: bool = True) -> UpdateResult:
    """
    Fetch origin and pull if local HEAD is behind.
    Skips if not a git repo or git missing.
    """
    try:
        from subscription import get_entitlements, git_updates_blocked_message

        if not get_entitlements().git_updates_allowed:
            return UpdateResult(False, False, False, git_updates_blocked_message())
    except Exception:
        pass

    if not _git_ok():
        return UpdateResult(False, False, False, "Git not installed — skip update check.")

    if not (ROOT_DIR / ".git").is_dir():
        return UpdateResult(False, False, False, "Not a git clone — use git clone to get updates.")

    try:
        fetch = _run_git(["fetch", "origin", GITHUB_BRANCH], ROOT_DIR)
        if fetch.returncode != 0:
            return UpdateResult(
                True,
                False,
                False,
                f"git fetch failed: {(fetch.stderr or fetch.stdout or '').strip()}",
            )

        local = _run_git(["rev-parse", "HEAD"], ROOT_DIR)
        remote = _run_git(["rev-parse", f"origin/{GITHUB_BRANCH}"], ROOT_DIR)
        if local.returncode != 0 or remote.returncode != 0:
            return UpdateResult(True, False, False, "Could not read git revisions.")

        local_sha = (local.stdout or "").strip()
        remote_sha = (remote.stdout or "").strip()
        if not local_sha or not remote_sha:
            return UpdateResult(True, False, False, "Empty git revision.")

        if local_sha == remote_sha:
            _write_state(
                local_sha=local_sha,
                remote_sha=remote_sha,
                update_available=False,
                update_message="",
            )
            return UpdateResult(
                True,
                False,
                False,
                "Already up to date.",
                local_sha=local_sha,
                remote_sha=remote_sha,
            )

        behind = _run_git(["rev-list", "--count", f"HEAD..origin/{GITHUB_BRANCH}"], ROOT_DIR)
        n_behind = int((behind.stdout or "0").strip() or "0")

        if not auto_pull:
            msg = (
                f"Update available ({n_behind} commit(s)). "
                "Run updatewindows.bat or updateapple.command, then restart."
            )
            _write_state(
                local_sha=local_sha,
                remote_sha=remote_sha,
                update_available=True,
                update_message=msg,
            )
            return UpdateResult(
                True,
                True,
                False,
                msg,
                local_sha=local_sha,
                remote_sha=remote_sha,
            )

        pull = _run_git(["pull", "--ff-only", "origin", GITHUB_BRANCH], ROOT_DIR)
        if pull.returncode != 0:
            msg = f"Update available but pull failed: {(pull.stderr or pull.stdout or '').strip()}"
            _write_state(
                local_sha=local_sha,
                remote_sha=remote_sha,
                update_available=True,
                update_message=msg,
            )
            return UpdateResult(
                True,
                True,
                False,
                msg,
                local_sha=local_sha,
                remote_sha=remote_sha,
            )

        _pip_refresh()
        new_local = _run_git(["rev-parse", "HEAD"], ROOT_DIR)
        new_sha = (new_local.stdout or "").strip()
        _write_state(
            local_sha=new_sha,
            remote_sha=new_sha,
            update_available=False,
            update_message="",
            last_pull_ok=True,
        )
        return UpdateResult(
            True,
            True,
            True,
            f"Updated successfully ({n_behind} commit(s) from GitHub).",
            local_sha=new_sha,
            remote_sha=remote_sha,
        )
    except subprocess.TimeoutExpired:
        return UpdateResult(True, False, False, "Git timed out — check your internet.")
    except Exception as exc:
        log.exception("update check failed")
        return UpdateResult(True, False, False, f"Update check error: {exc}")


def _pip_refresh() -> None:
    venv_py = APP_DIR / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    py = str(venv_py) if venv_py.is_file() else sys.executable
    req = APP_DIR / "requirements.txt"
    if not req.is_file():
        return
    subprocess.run(
        [py, "-m", "pip", "install", "-r", str(req), "-q"],
        cwd=str(APP_DIR),
        timeout=300,
        check=False,
    )
    ka = APP_DIR / "requirements-kleinanzeigen.txt"
    if ka.is_file():
        subprocess.run(
            [py, "-m", "pip", "install", "-r", str(ka), "-q"],
            cwd=str(APP_DIR),
            timeout=300,
            check=False,
        )


def main() -> int:
    auto = "--no-pull" not in sys.argv
    result = check_and_update(auto_pull=auto)
    print(result.message)
    if result.local_sha and result.remote_sha and result.update_available and not result.pulled:
        print(f"  local:  {result.local_sha[:8]}")
        print(f"  remote: {result.remote_sha[:8]}")
    return 0 if result.checked and not result.update_available or result.pulled else (
        2 if result.update_available else 1
    )


def sidebar_update_notice() -> str | None:
    """Short text for the dashboard when an update could not be applied automatically."""
    state = _read_state()
    if not state.get("update_available"):
        return None
    msg = (state.get("update_message") or "").strip()
    if msg:
        return msg
    return "Update available — run the update script in windows/ or apple/, then restart."


if __name__ == "__main__":
    raise SystemExit(main())
