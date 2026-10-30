#!/usr/bin/env python3
"""Non-blocking GitHub release checks for the Across32 Launcher.

The GUI starts this as a separate, short-lived process; it never waits for
network operations in Qt's event loop. Only versions read from the official
private repository's main branch are trusted. The latest known version is
persisted so an update warning survives app restarts and transient outages.
"""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from app_manager import APPS, App, parse_version_source, revision, version

CACHE_FORMAT = 1
RELEASE_PATTERN = re.compile(r"^[vV]?\d+(?:[.-]\d+)*(?:[-+][A-Za-z0-9.-]+)?$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def cache_path() -> Path:
    root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache").expanduser()
    if not root.is_absolute():
        root = Path.home() / ".cache"
    return root / "across32-launcher" / "remote_versions.json"


def read_cache(path: Path | None = None) -> dict:
    path = path or cache_path()
    try:
        if not path.is_file() or path.stat().st_size > 128_000:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("format") != CACHE_FORMAT:
            return {}
        valid_keys = {app.key for app in APPS}
        result = {}
        for key, record in value.get("repos", {}).items():
            if key not in valid_keys or not isinstance(record, dict):
                continue
            remote = record.get("remote_version", "")
            sha = record.get("remote_sha", "")
            if (isinstance(remote, str) and len(remote) < 72
                    and isinstance(sha, str) and (not sha or GIT_SHA.fullmatch(sha))):
                result[key] = {"remote_version": remote, "remote_sha": sha}
        return result
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def save_cache(records: dict, path: Path | None = None) -> None:
    path = path or cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, staging = tempfile.mkstemp(prefix=".remote-versions-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"format": CACHE_FORMAT, "repos": records},
                      handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(staging, 0o600)
        os.replace(staging, path)
    finally:
        Path(staging).unlink(missing_ok=True)


def version_parts(value: str) -> tuple[int, ...] | None:
    """Numeric comparisons work for 0.8.50, v309, and 2026.10.24-95."""
    if not isinstance(value, str) or not RELEASE_PATTERN.fullmatch(value.strip()):
        return None
    base = value.strip().lstrip("vV").split("+", 1)[0]
    # A dash can separate date/build digits, or introduce prerelease text.
    chunks = re.split(r"[.-]", base)
    if not all(part.isdecimal() for part in chunks):
        return None
    return tuple(int(part) for part in chunks)


def newer_release(remote: str, local: str) -> bool:
    head = version_parts(remote)
    installed = version_parts(local)
    if head is None or installed is None:
        return False
    width = max(len(head), len(installed))
    return head + (0,) * (width - len(head)) > installed + (0,) * (width - len(installed))


def update_available(app: App, local: str, record: dict) -> bool:
    remote_version = record.get("remote_version", "")
    if newer_release(remote_version, local):
        return True
    # No numbered releases in the player repository: only a verified commit
    # difference can signal a new version, not an arbitrary string mismatch.
    if app.key == "player" and not remote_version:
        remote_sha = record.get("remote_sha", "")
        local_sha = revision(app)
        return bool(GIT_SHA.fullmatch(remote_sha) and local_sha
                    and not remote_sha.startswith(local_sha))
    return False


def api_json(endpoint: str) -> object:
    """Use the user's authenticated GitHub CLI; surface actionable failures."""
    executable = shutil.which("gh")
    if not executable:
        for candidate in (
            Path.home() / ".local/bin/gh",
            Path("/usr/bin/gh"),
            Path("/usr/local/bin/gh"),
        ):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                executable = str(candidate)
                break
    if not executable:
        raise RuntimeError(
            "A GitHub CLI (gh) nem található. Telepítés: sudo pacman -S github-cli"
        )
    try:
        result = subprocess.run(
            [executable, "api", endpoint], capture_output=True, text=True,
            check=False, timeout=25,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("GitHub API időtúllépés (25 másodperc).") from exc
    except OSError as exc:
        raise RuntimeError(f"GitHub CLI indítási hiba: {exc}") from exc
    if result.returncode:
        # gh normally reports 401/403/404 and login details on stderr; until
        # now that error was silently discarded by the GUI.
        detail = (result.stderr or result.stdout or "").strip()
        detail = " ".join(detail.splitlines())[:280]
        if not detail:
            detail = f"GitHub CLI hibakód: {result.returncode}"
        raise RuntimeError(
            f"{detail} — Ellenőrizd: gh auth status"
        )
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("A GitHub CLI nem érvényes JSON-választ adott.") from exc


def fetch_remote(app: App) -> dict:
    if app.key == "player":
        commit = api_json(f"repos/Across32/{app.key}/commits/main")
        sha = commit.get("sha", "") if isinstance(commit, dict) else ""
        if not GIT_SHA.fullmatch(sha):
            raise ValueError("Hiányzó vagy hibás GitHub commit azonosító.")
        return {"remote_version": "", "remote_sha": sha}
    response = api_json(
        f"repos/Across32/{app.key}/contents/{app.version_file}?ref=main"
    )
    if not isinstance(response, dict) or response.get("encoding") != "base64":
        raise ValueError("A GitHub nem küldött értelmezhető verziófájlt.")
    raw = base64.b64decode(response["content"], validate=False).decode("utf-8")
    version_text = parse_version_source(app, raw)
    if version_parts(version_text) is None:
        raise ValueError(f"A repó verziója nem értelmezhető: {app.key}")
    return {"remote_version": version_text, "remote_sha": ""}


def scan() -> int:
    # Each repo checks independently; results are emitted as they arrive.
    # A failed request must NEVER erase a previous known newer release.
    records = read_cache()
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            jobs = {pool.submit(fetch_remote, app): app for app in APPS}
            for job in as_completed(jobs):
                app = jobs[job]
                try:
                    latest = job.result()
                    records[app.key] = {
                        **latest,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }
                    save_cache(records)
                    result = {"key": app.key, **latest, "ok": True}
                except (OSError, ValueError, TypeError, RuntimeError,
                        subprocess.SubprocessError) as exc:
                    result = {"key": app.key, "ok": False, "error": str(exc)[:320]}
                print(json.dumps(result, ensure_ascii=False), flush=True)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    if "--scan" not in sys.argv:
        print("Usage: update_checker.py --scan", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(scan())
